# skilltree CLI (Milestone 1)

A single-user, offline learning CLI derived from the SkillTree concepts (skills, prerequisites,
event log), rebuilt around retrieval practice, FSRS spaced review, successive relearning, and
mastery-gated unlocks. Points/XP never gate anything (M1 has no XP). The inherited
`skills-service` code in the rest of this repo is untouched; this package is self-contained here.

Spec: [`SPEC-m1.md`](SPEC-m1.md).

## Install

Requires Python 3.12+.

```bash
cd skilltree-cli
python3.12 -m venv .venv && . .venv/bin/activate
pip install -e '.[test]'
pytest -q
```

Runtime deps: Typer, PyYAML, `fsrs` (py-fsrs). Storage is stdlib `sqlite3`.

## Usage

The database defaults to `~/.skilltree/skilltree.db`; override with `--db PATH` (before the
command) or `SKILLTREE_DB`.

```bash
skilltree init                          # create DB / run migrations (safe to repeat)
skilltree import tests/fixtures/tree.yaml
skilltree study --limit 5               # type answers; Ctrl-D or :q to stop
skilltree status                        # due counts, p_known, what's locked and why
skilltree rebuild                       # replay events into derived tables
skilltree export [events.jsonl]         # events as JSONL (stdout by default)
skilltree --db /tmp/other.db status
```

### Authoring a tree

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

Import rejects cycles, unknown `requires`, duplicate ids, and items without an answer or
explanation, in one transaction (no partial writes). Re-import upserts by id.

## How it decides

- **Grading:** trim, collapse whitespace, casefold, exact match against any accepted answer.
- **Feedback:** explanation after every answer; on a miss, the correct answer first, then wait for Enter.
- **FSRS:** correct = Good, wrong = Again (py-fsrs defaults, fuzzing off for replay determinism).
- **Successive relearning:** 3 correct on the first study day, then 3 correct on 3 distinct later days = learned.
- **BKT per skill:** P_INIT 0.1, P_TRANSIT 0.15, P_GUESS 0.05, P_SLIP 0.1.
- **Unlock:** each prerequisite needs p_known >= 0.95, and >= 80% of its items must each have 3 correct answers on different days (each >= 24h after the item's first exposure and after its last miss), >= 70% accuracy over its last 6 answers, and a correct latest answer.
- **Events** (`imported`, `answered`, `unlocked`) are append-only; `card_state`/`skill_state` are derived.

Constants live in `src/skilltree/config.py`.

## Layout

```
src/skilltree/  cli.py db.py engine.py grading.py scheduler.py relearning.py bkt.py unlock.py
                yaml_import.py clock.py config.py migrations/0001_init.sql
tests/          unit tests, CLI end-to-end, sim/test_simulated_learners.py (90-day FakeClock)
```
