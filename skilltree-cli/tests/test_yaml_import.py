import pytest
from skilltree import engine
from skilltree.yaml_import import ImportErrorTree, parse
from conftest import FIXTURE, dump

GOOD = FIXTURE.read_text()
BAD = {
    "cycle": """
skills:
  - {id: A, title: A, requires: [B], items: [{id: a1, prompt: p, answers: [x], explanation: e}]}
  - {id: B, title: B, requires: [A], items: []}
""",
    "unknown": """
skills:
  - {id: A, title: A, requires: [Z], items: [{id: a1, prompt: p, answers: [x], explanation: e}]}
""",
    "duplicate": """
skills:
  - {id: A, title: A, requires: [], items: [{id: a1, prompt: p, answers: [x], explanation: e}]}
  - {id: A, title: A2, requires: [], items: []}
""",
    "empty_answers": """
skills:
  - {id: A, title: A, requires: [], items: [{id: a1, prompt: p, answers: [], explanation: e}]}
""",
    "no_explanation": """
skills:
  - {id: A, title: A, requires: [], items: [{id: a1, prompt: p, answers: [x]}]}
""",
}
TABLES = ["skills", "prereqs", "items", "events", "card_state", "skill_state"]


@pytest.mark.parametrize("name", list(BAD))
def test_rejects_and_db_unchanged(loaded, clock, name):
    before = {t: dump(loaded, t) for t in TABLES}
    with pytest.raises(ImportErrorTree):
        engine.import_tree(loaded, parse(BAD[name]), "bad.yaml", clock.now())
    assert {t: dump(loaded, t) for t in TABLES} == before


def test_failed_write_rolls_back(loaded, clock):
    # validation passes but the write fails midway (FK violation on a bogus parent) -> no partial write
    from skilltree.yaml_import import Skill
    before = {t: dump(loaded, t) for t in TABLES}
    with pytest.raises(Exception):
        engine.import_tree(loaded, [Skill("Q", "Q", [], parent_id="nope")], "x", clock.now())
    assert {t: dump(loaded, t) for t in TABLES} == before


def test_reimport_upserts_and_appends_one_event(loaded, clock):
    ev = dump(loaded, "events")
    engine.import_tree(loaded, parse(GOOD.replace("2 + 3 = ?", "2 + 3 equals?")), "tree.yaml", clock.now())
    after = dump(loaded, "events")
    assert after[: len(ev)] == ev and len(after) == len(ev) + 1 and after[-1][2] == "imported"
    assert loaded.execute("SELECT prompt FROM items WHERE id='a1'").fetchone()[0] == "2 + 3 equals?"
    assert loaded.execute("SELECT COUNT(*) FROM items").fetchone()[0] == 12
