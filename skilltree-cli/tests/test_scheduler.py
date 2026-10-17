from unittest import mock
from fsrs import Rating
from skilltree import scheduler
from skilltree.clock import FakeClock


def test_rating_mapping_calls():
    c = FakeClock()
    card = scheduler.new_card("x", c.now())
    with mock.patch.object(scheduler._SCHED, "review_card", wraps=scheduler._SCHED.review_card) as m:
        scheduler.review(card, True, c.now())
        scheduler.review(card, False, c.now())
    assert m.call_args_list[0].args[1] == Rating.Good
    assert m.call_args_list[1].args[1] == Rating.Again


def test_due_moves_forward():
    c = FakeClock()
    card = scheduler.new_card("x", c.now())
    import random
    rng = random.Random(1)
    for _ in range(30):
        now = c.now()
        card = scheduler.review(card, rng.random() < 0.7, now)
        assert card.due > now
        c.set(card.due)


def test_roundtrip():
    c = FakeClock()
    card = scheduler.review(scheduler.new_card("x", c.now()), True, c.now())
    assert scheduler.dumps(scheduler.loads(scheduler.dumps(card))) == scheduler.dumps(card)
