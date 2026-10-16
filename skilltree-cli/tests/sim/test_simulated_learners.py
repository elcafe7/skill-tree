"""60-day simulated learners driving the engine directly with a FakeClock."""
import json
import math
import random
from datetime import timedelta

import pytest

from skilltree import db, engine
from skilltree.clock import FakeClock, parse
from skilltree.yaml_import import load_file
from conftest import FIXTURE

DAYS = 60


class Perfect:
    def p_correct(self, item_id, now):
        return 1.0


class Guesser:
    def p_correct(self, item_id, now):
        return 0.25


class Forgetful:
    """Recall decays as exp(-t/S) since the last review; S grows on success, shrinks on failure."""

    def __init__(self):
        self.last, self.S = {}, {}

    def p_correct(self, item_id, now):
        if item_id not in self.last:
            return 0.5
        t = (now - self.last[item_id]).total_seconds() / 86400
        return math.exp(-t / self.S[item_id])

    def observe(self, item_id, now, correct):
        s = self.S.get(item_id, 1.0)
        self.S[item_id] = s * 1.8 if correct else max(0.5, s * 0.5)
        self.last[item_id] = now


def run(profile, seed=1234):
    rng = random.Random(seed)
    clock = FakeClock()
    conn = db.connect(":memory:")
    engine.import_tree(conn, load_file(FIXTURE), "tree.yaml", clock.now())
    sessions = []
    for day in range(DAYS):
        start = clock.now()
        s = engine.Session(conn, clock, limit=20)
        while (it := s.next()) is not None:
            ok = rng.random() < profile.p_correct(it["id"], clock.now())
            s.answer(json.loads(it["answers"])[0] if ok else "zzz-wrong", 1500)
            if hasattr(profile, "observe"):
                profile.observe(it["id"], clock.now(), ok)
            clock.advance(seconds=20)
        dues = {r[0]: parse(r[1]) for r in conn.execute("SELECT item_id, due FROM card_state")}
        for item in s.studied:
            assert dues[item] >= start, f"{item} due before session clock on day {day}"
        sessions.append((start, set(s.studied), dues))
        clock.set(start + timedelta(days=1))
    return conn, sessions


def unlock_times(conn):
    return {r[0]: parse(r[1]) for r in conn.execute("SELECT skill_id, ts FROM events WHERE type='unlocked'")}


def first_exposure(conn, skill):
    return parse(conn.execute("SELECT MIN(ts) FROM events WHERE type='answered' AND skill_id=?",
                              (skill,)).fetchone()[0])


def intervals(sessions, item):
    out = []
    for start, studied, dues in sessions:
        if item in studied:
            out.append(dues[item] - start)
    return out


def test_perfect_learner():
    conn, sessions = run(Perfect())
    u = unlock_times(conn)
    assert set(u) == {"A", "B", "C", "D"}
    assert u["A"] <= u["B"] and u["A"] <= u["C"]
    assert u["D"] > max(u["B"], u["C"])
    day = timedelta(hours=24)
    assert u["B"] >= first_exposure(conn, "A") + day
    assert u["C"] >= first_exposure(conn, "A") + day
    assert u["D"] >= max(first_exposure(conn, "B"), first_exposure(conn, "C")) + day
    iv = intervals(sessions, "a1")
    assert len(iv) >= 3
    assert all(b >= a for a, b in zip(iv, iv[1:])), iv
    assert iv[-1] > iv[0]


def test_guesser_never_unlocks():
    conn, _ = run(Guesser())
    assert set(unlock_times(conn)) == {"A"}


def test_forgetful_learner():
    conn, sessions = run(Forgetful())
    lapses = conn.execute("SELECT SUM(lapses) FROM card_state").fetchone()[0]
    assert lapses > 0
    # some item's interval shrinks right after a lapse
    shrank = False
    for item, in conn.execute("SELECT item_id FROM card_state WHERE lapses > 0"):
        iv = intervals(sessions, item)
        if any(b < a for a, b in zip(iv, iv[1:])):
            shrank = True
    assert shrank
    u = unlock_times(conn)
    assert "B" in u or "C" in u
    pu = unlock_times(run(Perfect())[0])
    first = min(u[k] for k in ("B", "C") if k in u)
    assert first > min(pu["B"], pu["C"])
