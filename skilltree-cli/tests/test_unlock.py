import json
from datetime import datetime, timedelta, timezone
from skilltree import engine
from skilltree.unlock import SkillView, can_unlock, item_mastered, unmet

T0 = datetime(2026, 1, 1, 9, tzinfo=timezone.utc)
D = timedelta(days=1)


def H(*pairs):
    return [(T0 + off, c) for off, c in pairs]


GOOD = H((timedelta(0), True), (D, True), (2 * D, True))  # 2 delayed successes on distinct days


def test_item_mastery():
    assert item_mastered(GOOD)
    assert not item_mastered(H((timedelta(0), True), (D, True)))                       # only 1 delayed day
    assert not item_mastered(H((timedelta(0), True), (D, True), (D + timedelta(hours=1), True)))  # same day
    assert not item_mastered(H((timedelta(0), True), (timedelta(hours=23), True), (D, True)))  # <24h doesn't count
    assert not item_mastered(GOOD + H((3 * D, False)))                                  # most recent wrong
    lapse_then_one = GOOD + H((3 * D, False), (4 * D, True))
    assert not item_mastered(lapse_then_one)                                            # lapse resets
    assert item_mastered(lapse_then_one + H((5 * D, True)))


def _view(p, mastered, n=3):
    return SkillView(p, {f"i{k}": (GOOD if k < mastered else H((timedelta(0), True))) for k in range(n)}, n)


def test_unlock_rule_unit():
    assert not can_unlock({"A": _view(0.96, 0)})          # p_known high, no delayed successes
    assert not can_unlock({"A": _view(0.96, 2)})          # 2/3 < 80%
    assert can_unlock({"A": _view(0.96, 3)})
    assert not can_unlock({"A": _view(0.90, 3)})          # BKT too low
    assert can_unlock({"A": _view(0.96, 4, n=5)})         # 4/5 = 80%
    assert not can_unlock({"B": _view(0.99, 3), "C": _view(0.50, 3)})
    assert [p for p, _ in unmet({"B": _view(0.99, 3), "C": _view(0.5, 3)})] == ["C"]


def _ans(conn, item_id):
    return json.loads(conn.execute("SELECT answers FROM items WHERE id=?", (item_id,)).fetchone()[0])[0]


def _unlocked(conn):
    return {r[0] for r in conn.execute("SELECT skill_id FROM skill_state WHERE unlocked=1")}


def _round(conn, clock, items, wrong=()):
    for i in items:
        engine.record_answer(conn, i, "nope" if i in wrong else _ans(conn, i), clock.now())
        clock.advance(seconds=10)


def test_unlock_through_engine(loaded, clock):
    A = ["a1", "a2", "a3"]
    assert _unlocked(loaded) == {"A"}
    for _ in range(3):
        _round(loaded, clock, A)
    clock.advance(days=1); _round(loaded, clock, A)
    assert _unlocked(loaded) == {"A"}                     # only one delayed day so far
    clock.advance(days=1); _round(loaded, clock, ["a1", "a2"], wrong=["a2"])
    _round(loaded, clock, ["a3"])
    assert _unlocked(loaded) == {"A"}                     # a2 lapsed -> 2/3 mastered
    clock.advance(days=1); _round(loaded, clock, ["a2"])
    assert _unlocked(loaded) == {"A"}                     # a2 has 1 delayed day since lapse
    clock.advance(days=1)
    res = engine.record_answer(loaded, "a2", "8", clock.now())
    assert set(res.unlocked) == {"B", "C"}
    n = loaded.execute("SELECT COUNT(*) FROM events WHERE type='unlocked' AND skill_id='B'").fetchone()[0]
    assert n == 1
