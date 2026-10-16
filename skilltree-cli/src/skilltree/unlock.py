from __future__ import annotations
from dataclasses import dataclass
from . import config


@dataclass(frozen=True)
class SkillView:
    p_known: float
    last_delayed_success_ts: str | None


def unmet(prereqs: dict[str, SkillView]) -> list[tuple[str, str]]:
    """Return (prereq_id, reason) for each unmet prerequisite."""
    out = []
    for sid, v in prereqs.items():
        reasons = []
        if v.p_known < config.UNLOCK_P_KNOWN:
            reasons.append(f"p_known {v.p_known:.2f} < {config.UNLOCK_P_KNOWN}")
        if not v.last_delayed_success_ts:
            reasons.append(f"no correct answer {config.DELAYED_SUCCESS_HOURS}h+ after first exposure")
        if reasons:
            out.append((sid, "; ".join(reasons)))
    return out


def can_unlock(prereqs: dict[str, SkillView]) -> bool:
    return bool(prereqs) and not unmet(prereqs)
