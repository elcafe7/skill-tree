from skilltree.relearning import Relearn, step


def test_initial_needs_three_correct():
    s = Relearn()
    s = step(s, True, "2026-01-01"); assert s.phase == "initial"
    s = step(s, False, "2026-01-01"); s = step(s, True, "2026-01-01")
    assert s.phase == "initial" and s.session_correct == 2
    s = step(s, True, "2026-01-01")
    assert s.phase == "spaced"


def _spaced():
    s = Relearn()
    for _ in range(3):
        s = step(s, True, "2026-01-01")
    return s


def test_spaced_needs_three_distinct_later_days():
    s = _spaced()
    s = step(s, True, "2026-01-01"); assert s.spaced_correct == 0  # same day as first session
    s = step(s, True, "2026-01-02"); s = step(s, True, "2026-01-02")
    assert s.spaced_correct == 1
    s = step(s, True, "2026-01-04"); assert s.phase == "spaced"
    s = step(s, True, "2026-01-08"); assert s.phase == "learned"


def test_spaced_miss_resets():
    s = _spaced()
    s = step(s, True, "2026-01-02"); s = step(s, True, "2026-01-03")
    assert s.spaced_correct == 2
    s = step(s, False, "2026-01-04")
    assert s.spaced_correct == 0 and s.phase == "spaced"
    for d in ("05", "06"):
        s = step(s, True, f"2026-01-{d}")
    assert s.phase == "spaced"
    s = step(s, True, "2026-01-07"); assert s.phase == "learned"
