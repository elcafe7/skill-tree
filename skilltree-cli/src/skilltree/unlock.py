"""Unlock rule (pure). A prerequisite is mastered when:
1. BKT p_known >= UNLOCK_P_KNOWN;
2. >= MASTERY_ITEM_FRACTION of its items each have DELAYED_ITEM_SUCCESSES correct answers on distinct
   study days, each >= DELAYED_SUCCESS_HOURS after that item's first exposure, counted since the item's
   most recent wrong answer (a lapse resets them);
3. the most recent answer on each of those items was correct, and accuracy over the item's last
   ITEM_ACCURACY_WINDOW answers (or all, if fewer) is >= ITEM_MIN_ACCURACY.
"""
from __future__ import annotations
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from . import config


@dataclass(frozen=True)
class SkillView:
    p_known: float
    answers: dict[str, list[tuple[datetime, bool]]] = field(default_factory=dict)  # item -> [(ts, correct)] in order
    n_items: int = 0


def item_mastered(history: list[tuple[datetime, bool]]) -> bool:
    if not history or not history[-1][1]:
        return False
    first = history[0][0]
    last_wrong = max((i for i, (_, c) in enumerate(history) if not c), default=-1)
    days = {ts.date() for ts, c in history[last_wrong + 1:]
            if c and ts - first >= timedelta(hours=config.DELAYED_SUCCESS_HOURS)}
    window = history[-config.ITEM_ACCURACY_WINDOW:]
    accuracy = sum(c for _, c in window) / len(window)
    return len(days) >= config.DELAYED_ITEM_SUCCESSES and accuracy >= config.ITEM_MIN_ACCURACY - 1e-12


def required_items(n_items: int) -> int:
    return math.ceil(config.MASTERY_ITEM_FRACTION * n_items - 1e-9)


def skill_reasons(v: SkillView) -> list[str]:
    reasons = []
    if v.p_known < config.UNLOCK_P_KNOWN:
        reasons.append(f"p_known {v.p_known:.2f} < {config.UNLOCK_P_KNOWN}")
    done = sum(item_mastered(h) for h in v.answers.values())
    need = required_items(v.n_items)
    if done < need or v.n_items == 0:
        reasons.append(f"{done}/{v.n_items} items mastered with delayed successes, need {need}")
    return reasons


def unmet(prereqs: dict[str, SkillView]) -> list[tuple[str, str]]:
    return [(sid, "; ".join(r)) for sid, v in prereqs.items() if (r := skill_reasons(v))]


def can_unlock(prereqs: dict[str, SkillView]) -> bool:
    return bool(prereqs) and not unmet(prereqs)
