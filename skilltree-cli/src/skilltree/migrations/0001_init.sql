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
