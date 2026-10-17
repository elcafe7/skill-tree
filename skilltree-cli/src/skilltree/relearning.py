"""Successive-relearning counters (pure)."""
from __future__ import annotations
from dataclasses import dataclass, replace
from . import config


@dataclass(frozen=True)
class Relearn:
    phase: str = "new"
    first_session_date: str | None = None
    session_correct: int = 0
    spaced_correct: int = 0
    last_spaced_date: str | None = None


def step(s: Relearn, correct: bool, day: str) -> Relearn:
    """Apply one answer given on calendar day `day` (YYYY-MM-DD, UTC)."""
    if s.phase == "new":
        s = replace(s, phase="initial", first_session_date=day)
    if s.phase == "initial":
        if correct:
            n = s.session_correct + 1
            s = replace(s, session_correct=n)
            if n >= config.INITIAL_CORRECT:
                s = replace(s, phase="spaced")
        return s
    if s.phase == "spaced":
        if not correct:
            return replace(s, spaced_correct=0)
        if day > (s.first_session_date or "") and day != s.last_spaced_date:
            n = s.spaced_correct + 1
            s = replace(s, spaced_correct=n, last_spaced_date=day)
            if n >= config.SPACED_CORRECT:
                s = replace(s, phase="learned")
        return s
    return s  # learned: FSRS keeps scheduling, counters frozen
