"""Thin wrapper over py-fsrs. Correct -> Good, wrong -> Again."""
from __future__ import annotations
import json
import zlib
from datetime import datetime
from fsrs import Card, Rating, Scheduler

# py-fsrs defaults, except fuzzing is off so replaying events is deterministic
# (required by the rebuild invariant).
_SCHED = Scheduler(enable_fuzzing=False)


def rating_for(correct: bool) -> Rating:
    return Rating.Good if correct else Rating.Again


def new_card(item_id: str, now: datetime) -> Card:
    return Card(card_id=zlib.crc32(item_id.encode()), due=now)


def review(card: Card, correct: bool, now: datetime) -> Card:
    card, _ = _SCHED.review_card(card, rating_for(correct), review_datetime=now)
    return card


def dumps(card: Card) -> str:
    return json.dumps(card.to_dict(), sort_keys=True)


def loads(s: str) -> Card:
    return Card.from_dict(json.loads(s))
