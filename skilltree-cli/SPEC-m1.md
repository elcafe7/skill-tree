# Skilltree CLI — Milestone 1 spec

## Outcome
One learner can author a small YAML skill tree, study typed-recall items in the terminal, get FSRS scheduling and successive-relearning progress, and unlock skills only on mastery. Every state change is an event, and all progress can be rebuilt from the event log.

## Decisions already made (do not revisit)
- Python 3.12. Standard-library `sqlite3`, Typer for the CLI, pytest for tests, PyYAML for import, `fsrs` (py-fsrs) for scheduling. No other runtime dependencies without approval.
- One local SQLite file. Default path `~/.skilltree/skilltree.db`, overridable with `--db PATH` or the `SKILLTREE_DB` environment variable.
- The `events` table is append-only and is the source of truth. `card_state` and `skill_state` are derived and must be rebuildable.
- All learning rules live in the core package. The CLI only does I/O.
- Points or XP never gate anything. M1 has no XP.
- Single user. No auth, network, sync, or UI.

## Non-goals for M1
Multiple choice or other item kinds, fuzzy or AI grading, worked-example fading, interleaving across discrimination sets, XP, any GUI, sync, multiple profiles, and FSRS parameter optimization.

## Invariants
- Never update or delete a row in `events`.
- `skilltree rebuild` produces derived tables identical to the live ones.
- A skill with prerequisites unlocks only when the unlock rule below holds. Points, counts, and time alone never unlock it.
- No item from a locked skill is ever shown as new.
- After a study session, no studied item has `due` earlier than the session's clock.
- Answers, prompts, and the database path never go to logs. There are no logs beyond normal CLI output.
- The clock is injectable (`now()` from a clock object) everywhere. No direct `datetime.now()` in the core.

## Layout
```
pyproject.toml
src/skilltree/
  __init__.py
  cli.py          # Typer app, I/O only
  db.py           # connection, migrations
  migrations/0001_init.sql
  yaml_import.py  # parse + validate DAG
  grading.py      # answer normalization and match
  scheduler.py    # FSRS wrapper
  relearning.py   # successive-relearning counters
  bkt.py          # BKT update
  unlock.py       # unlock rule
  engine.py       # apply_event(), rebuild(), next_items()
  clock.py        # SystemClock, FakeClock
tests/
  fixtures/tree.yaml
  test_*.py
  sim/test_simulated_learners.py
```

## Data model (`0001_init.sql`)
```sql
CREATE TABLE schema_version (version INTEGER NOT NULL);

CREATE TABLE skills (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  parent_id TEXT REFERENCES skills(id)
);
CREATE TABLE prereqs (
  skill_id TEXT NOT NULL REFERENCES skills(id),
  requires_id TEXT NOT NULL REFERENCES skills(id),
  PRIMARY KEY (skill_id, requires_id)
);
CREATE TABLE items (
  id TEXT PRIMARY KEY,
  skill_id TEXT NOT NULL REFERENCES skills(id),
  kind TEXT NOT NULL CHECK (kind = 'recall'),
  prompt TEXT NOT NULL,
  answers TEXT NOT NULL,          -- JSON array of accepted strings, length >= 1
  explanation TEXT NOT NULL,
  worked_example TEXT             -- stored, not used in M1
);
CREATE TABLE events (
  seq INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,               -- ISO 8601 UTC
  type TEXT NOT NULL CHECK (type IN ('imported','answered','unlocked')),
  item_id TEXT,
  skill_id TEXT,
  payload TEXT NOT NULL           -- JSON
);
CREATE TABLE card_state (
  item_id TEXT PRIMARY KEY REFERENCES items(id),
  fsrs_card TEXT NOT NULL,        -- serialized py-fsrs card
  due TEXT NOT NULL,
  reps INTEGER NOT NULL,
  lapses INTEGER NOT NULL,
  relearn_phase TEXT NOT NULL CHECK (relearn_phase IN ('new','initial','spaced','learned')),
  first_session_date TEXT,
  session_correct INTEGER NOT NULL DEFAULT 0,
  spaced_correct INTEGER NOT NULL DEFAULT 0,
  last_spaced_date TEXT
);
CREATE TABLE skill_state (
  skill_id TEXT PRIMARY KEY REFERENCES skills(id),
  p_known REAL NOT NULL,
  first_exposure_ts TEXT,
  last_delayed_success_ts TEXT,
  unlocked INTEGER NOT NULL
);
```
`answered` payload: `{"response": str, "correct": bool, "latency_ms": int, "rating": "again"|"good"}`.
`imported` payload: `{"source": filename, "skills": n, "items": n}`.
`unlocked` payload: `{"reason": "mastery"|"root"}`.

## YAML format
```yaml
skills:
  - id: fractions
    title: Fractions
    requires: []
    items:
      - id: frac-1
        prompt: "1/2 + 1/4 = ?"
        answers: ["3/4", "0.75"]
        explanation: "Convert 1/2 to 2/4, then 2/4 + 1/4 = 3/4."
```
Import must reject, with a clear error and no partial write (one transaction), any cycle, unknown `requires` id, duplicate id, or item without at least one answer or an explanation. Re-import upserts skills and items by id and never touches events except to append one `imported` event.

## Rules (core)
**Grading.** Normalize by trimming, collapsing internal whitespace, and casefolding. Correct if the normalized response equals any normalized accepted answer. No fuzzy match.

**Feedback.** After every answer the CLI shows the result. If wrong, it shows the correct answer (the first accepted answer) and then the explanation, and waits for Enter before the next item. If correct, it shows the explanation too.

**FSRS.** Use py-fsrs defaults. Correct maps to `Rating.Good`, wrong maps to `Rating.Again`. No self-rating in M1.

**Successive relearning** (constants in one config module):
- `INITIAL_CORRECT = 3`. In the item's first study day, the item repeats within the session until it has 3 correct answers (`relearn_phase` goes from `initial` to `spaced`).
- `SPACED_CORRECT = 3`. After that, 3 correct reviews on 3 distinct later days make it `learned`. A wrong spaced review resets `spaced_correct` to 0. FSRS still decides `due`.

**BKT** (per skill, updated on each `answered` event for an item in that skill). Defaults: `P_INIT = 0.1`, `P_TRANSIT = 0.15`, `P_GUESS = 0.05`, `P_SLIP = 0.1`. Standard update:
- correct: posterior = p(1-slip) / (p(1-slip) + (1-p)guess)
- wrong: posterior = p·slip / (p·slip + (1-p)(1-guess))
- then p_known = posterior + (1-posterior)·transit.

**Unlock.** A skill with no prerequisites is unlocked at import (append `unlocked` with reason `root`). A skill with prerequisites unlocks when every prerequisite is mastered. A prerequisite is mastered only when all of these hold (constants in `config.py`):
1. BKT `p_known >= 0.95` (`UNLOCK_P_KNOWN`).
2. At least 80% (`MASTERY_ITEM_FRACTION`, rounded up to whole items) of the skill's items each have at least 2 (`DELAYED_ITEM_SUCCESSES`) correct answers on different study days, each at least 24 hours (`DELAYED_SUCCESS_HOURS`) after that item's first exposure, counted since the item's most recent wrong answer.
3. The most recent answer on each of those items was correct.
A lapse therefore removes an item from the mastered set until it earns its delayed successes again. Item mastery is computed from the `answered` events (the source of truth). Check after every `answered` event, and append `unlocked` once.

**Item selection** (`next_items`). Due items first, ordered by `due`. Then new items only from unlocked skills, in YAML order, up to `--limit` (default 20). In-session relearning repeats are inserted after at least two other items when possible.

## Commands
- `skilltree init` creates the database and runs migrations. It's safe to run twice.
- `skilltree import PATH` validates and imports.
- `skilltree study [--limit N]` is the interactive loop with grading, feedback, and events. Ctrl-D or `:q` ends the session cleanly.
- `skilltree status` shows due-now and due-today counts, plus per skill: p_known to 2 decimals, locked or unlocked, and for a locked skill, which prerequisite is unmet and why.
- `skilltree rebuild` drops `card_state` and `skill_state` and replays `events` in `seq` order.
- `skilltree export [PATH]` writes events as JSONL (default stdout).

## Tests (pytest; all must pass)
1. Grading normalization and alternate answers.
2. FSRS mapping: correct calls Good, wrong calls Again, and `due` always moves forward.
3. Relearning counters: initial phase needs 3 correct; spaced needs 3 distinct days; a spaced miss resets.
4. BKT: fixed sequences match hand-computed values to 1e-9 with the defaults above.
5. Unlock: p_known 0.96 without delayed item successes stays locked; fewer than 80% mastered items stays locked; a lapse removes an item until it re-earns 2 delayed successes; one weak prerequisite blocks it.
6. YAML validation: a cycle, an unknown id, a duplicate id, and an empty answers list each fail, and the database is unchanged afterward.
7. Rebuild invariant: after a scripted session, `rebuild` yields identical `card_state` and `skill_state`.
8. Events are append-only. A test asserts that no code path issues UPDATE or DELETE on `events` (grep the source as a test).

`tests/fixtures/tree.yaml` has 4 skills, A as the root, B and C requiring A, and D requiring B and C, with 3 items each.

**Simulated learners** (`tests/sim`), using FakeClock over 60 days with one study session per day through `engine` directly:
- Perfect (always correct): unlocks follow the DAG order, nothing unlocks before the 24-hour delayed-success rule allows, and intervals grow across reviews.
- Guesser (random correct at 0.25 rate): never unlocks B, C, or D, across seeds 0-9.
- Forgetful (recall probability decays exponentially since last review, seeded RNG): lapses shorten intervals, it eventually unlocks B or C, it never unlocks a skill while any prerequisite item's most recent answer is wrong, and its first unlock is no earlier than the perfect learner's.
- For every profile, after each session no studied item is due before that session's clock.
Seed every RNG and make the simulation deterministic.

## Agent rules
- Touch only the files in Layout plus `README.md`.
- Don't add dependencies beyond those listed. Don't change the schema outside `0001_init.sql`.
- On the first failing command, stop and report the command, exit code, and last 40 lines. Don't weaken a test or an assertion to make it pass.

## Done when
- `pip install -e . && pytest -q` exits 0, including the simulation.
- Running `skilltree init`, then `skilltree import tests/fixtures/tree.yaml`, then `skilltree study --limit 5`, then `skilltree status` works end to end by hand.
- The report is the file list, the full `pytest -q` output, and a short transcript of that manual run.
