import json
from skilltree import engine
from conftest import dump


def test_rebuild_identical(loaded, clock):
    for day in range(4):
        s = engine.Session(loaded, clock, limit=5)
        k = 0
        while (it := s.next()) is not None:
            ans = json.loads(it["answers"])[0]
            s.answer(ans if k % 4 else "wrong", 1000)
            k += 1
            clock.advance(seconds=15)
        clock.advance(days=1)
    live = (dump(loaded, "card_state"), dump(loaded, "skill_state"))
    assert live[0] and live[1]
    engine.rebuild(loaded)
    assert (dump(loaded, "card_state"), dump(loaded, "skill_state")) == live
