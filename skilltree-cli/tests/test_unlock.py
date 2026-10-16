from datetime import timedelta
from skilltree import engine
from skilltree.unlock import SkillView, can_unlock, unmet


def test_unlock_rule_unit():
    assert not can_unlock({"A": SkillView(0.96, None)})
    assert can_unlock({"A": SkillView(0.96, "2026-01-02T09:00:00+00:00")})
    ok = SkillView(0.99, "2026-01-02T09:00:00+00:00")
    weak = SkillView(0.50, "2026-01-02T09:00:00+00:00")
    assert not can_unlock({"B": ok, "C": weak})
    assert [p for p, _ in unmet({"B": ok, "C": weak})] == ["C"]


def _master(conn, clock, skill_items):
    for _ in range(3):
        for i in skill_items:
            engine.record_answer(conn, i, _ans(conn, i), clock.now())
            clock.advance(seconds=10)


def _ans(conn, item_id):
    import json
    return json.loads(conn.execute("SELECT answers FROM items WHERE id=?", (item_id,)).fetchone()[0])[0]


def _unlocked(conn):
    return {r[0] for r in conn.execute("SELECT skill_id FROM skill_state WHERE unlocked=1")}


def test_unlock_through_engine(loaded, clock):
    assert _unlocked(loaded) == {"A"}
    _master(loaded, clock, ["a1", "a2", "a3"])
    p = loaded.execute("SELECT p_known FROM skill_state WHERE skill_id='A'").fetchone()[0]
    assert p >= 0.95
    assert _unlocked(loaded) == {"A"}  # high p_known but no delayed success yet
    clock.advance(hours=23, minutes=58)
    engine.record_answer(loaded, "a1", "5", clock.now())
    assert _unlocked(loaded) == {"A"}
    clock.advance(minutes=5)
    res = engine.record_answer(loaded, "a1", "5", clock.now())
    assert set(res.unlocked) == {"B", "C"}
    # D needs B and C; only B mastered -> stays locked
    _master(loaded, clock, ["b1", "b2", "b3"])
    clock.advance(days=1)
    engine.record_answer(loaded, "b1", "19", clock.now())
    assert "D" not in _unlocked(loaded)
    n = loaded.execute("SELECT COUNT(*) FROM events WHERE type='unlocked' AND skill_id='B'").fetchone()[0]
    assert n == 1
