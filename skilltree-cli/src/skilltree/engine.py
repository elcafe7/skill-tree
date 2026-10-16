"""Core engine: events in, derived state out. The CLI only does I/O on top of this."""
from __future__ import annotations
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta

from . import bkt, config, relearning, scheduler, unlock
from .clock import iso, parse
from .grading import is_correct
from .yaml_import import Skill, item_row, summary


# ---------- events ----------

def _append(conn: sqlite3.Connection, ts: datetime, type_: str, item_id: str | None,
            skill_id: str | None, payload: dict) -> sqlite3.Row:
    cur = conn.execute(
        "INSERT INTO events(ts, type, item_id, skill_id, payload) VALUES (?,?,?,?,?)",
        (iso(ts), type_, item_id, skill_id, json.dumps(payload, sort_keys=True)))
    row = conn.execute("SELECT * FROM events WHERE seq = ?", (cur.lastrowid,)).fetchone()
    apply_event(conn, row)
    return row


def apply_event(conn: sqlite3.Connection, ev: sqlite3.Row) -> None:
    """Fold one event into the derived tables. Pure function of (state, event)."""
    payload = json.loads(ev["payload"])
    if ev["type"] == "imported":
        conn.execute(
            "INSERT OR IGNORE INTO skill_state(skill_id, p_known, unlocked) "
            "SELECT id, ?, 0 FROM skills ORDER BY rowid", (config.P_INIT,))
    elif ev["type"] == "unlocked":
        conn.execute("UPDATE skill_state SET unlocked = 1 WHERE skill_id = ?", (ev["skill_id"],))
    elif ev["type"] == "answered":
        _apply_answer(conn, ev, payload)


def _apply_answer(conn, ev, payload) -> None:
    ts = parse(ev["ts"])
    day = ts.date().isoformat()
    correct = bool(payload["correct"])
    item_id, skill_id = ev["item_id"], ev["skill_id"]

    row = conn.execute("SELECT * FROM card_state WHERE item_id = ?", (item_id,)).fetchone()
    if row is None:
        card = scheduler.new_card(item_id, ts)
        rl = relearning.Relearn()
        reps = lapses = 0
    else:
        card = scheduler.loads(row["fsrs_card"])
        rl = relearning.Relearn(row["relearn_phase"], row["first_session_date"],
                                row["session_correct"], row["spaced_correct"], row["last_spaced_date"])
        reps, lapses = row["reps"], row["lapses"]
    was_reviewing = row is not None and card.state.name == "Review"
    card = scheduler.review(card, correct, ts)
    rl = relearning.step(rl, correct, day)
    reps += 1
    if not correct and was_reviewing:
        lapses += 1
    conn.execute(
        "INSERT OR REPLACE INTO card_state(item_id, fsrs_card, due, reps, lapses, relearn_phase, "
        "first_session_date, session_correct, spaced_correct, last_spaced_date) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (item_id, scheduler.dumps(card), iso(card.due), reps, lapses, rl.phase, rl.first_session_date,
         rl.session_correct, rl.spaced_correct, rl.last_spaced_date))

    s = conn.execute("SELECT * FROM skill_state WHERE skill_id = ?", (skill_id,)).fetchone()
    p = bkt.update(s["p_known"], correct)
    first = s["first_exposure_ts"] or ev["ts"]
    delayed = s["last_delayed_success_ts"]
    if correct and ts - parse(first) >= timedelta(hours=config.DELAYED_SUCCESS_HOURS):
        delayed = ev["ts"]
    conn.execute(
        "UPDATE skill_state SET p_known = ?, first_exposure_ts = ?, last_delayed_success_ts = ? "
        "WHERE skill_id = ?", (p, first, delayed, skill_id))


def rebuild(conn: sqlite3.Connection) -> None:
    conn.execute("BEGIN")
    try:
        conn.execute("DELETE FROM card_state")
        conn.execute("DELETE FROM skill_state")
        for ev in conn.execute("SELECT * FROM events ORDER BY seq").fetchall():
            apply_event(conn, ev)
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise


# ---------- import ----------

def import_tree(conn: sqlite3.Connection, skills: list[Skill], source: str, now: datetime) -> tuple[int, int]:
    conn.execute("BEGIN")
    try:
        for s in skills:
            conn.execute("INSERT INTO skills(id, title, parent_id) VALUES (?,?,NULL) "
                         "ON CONFLICT(id) DO UPDATE SET title = excluded.title", (s.id, s.title))
        for s in skills:
            conn.execute("UPDATE skills SET parent_id = ? WHERE id = ?", (s.parent_id, s.id))
            conn.execute("DELETE FROM prereqs WHERE skill_id = ?", (s.id,))
            for r in s.requires:
                conn.execute("INSERT INTO prereqs(skill_id, requires_id) VALUES (?,?)", (s.id, r))
            for it in s.items:
                conn.execute(
                    "INSERT INTO items(id, skill_id, kind, prompt, answers, explanation, worked_example) "
                    "VALUES (?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET skill_id=excluded.skill_id, "
                    "prompt=excluded.prompt, answers=excluded.answers, explanation=excluded.explanation, "
                    "worked_example=excluded.worked_example", item_row(s.id, it))
        n_sk, n_it = summary(skills)
        _append(conn, now, "imported", None, None, {"source": source, "skills": n_sk, "items": n_it})
        roots = conn.execute(
            "SELECT s.id FROM skills s JOIN skill_state st ON st.skill_id = s.id "
            "WHERE st.unlocked = 0 AND NOT EXISTS (SELECT 1 FROM prereqs p WHERE p.skill_id = s.id) "
            "ORDER BY s.rowid").fetchall()
        for r in roots:
            _append(conn, now, "unlocked", None, r["id"], {"reason": "root"})
        conn.execute("COMMIT")
        return n_sk, n_it
    except Exception:
        conn.execute("ROLLBACK")
        raise


# ---------- answering ----------

@dataclass
class AnswerResult:
    correct: bool
    correct_answer: str
    explanation: str
    unlocked: list[str]


def skill_view(conn, skill_id) -> unlock.SkillView:
    p = conn.execute("SELECT p_known FROM skill_state WHERE skill_id = ?", (skill_id,)).fetchone()[0]
    n = conn.execute("SELECT COUNT(*) FROM items WHERE skill_id = ?", (skill_id,)).fetchone()[0]
    answers: dict[str, list] = {}
    for r in conn.execute("SELECT item_id, ts, payload FROM events WHERE type = 'answered' AND skill_id = ? "
                          "ORDER BY seq", (skill_id,)):
        answers.setdefault(r["item_id"], []).append((parse(r["ts"]), bool(json.loads(r["payload"])["correct"])))
    return unlock.SkillView(p, answers, n)


def _prereq_views(conn, skill_id) -> dict[str, unlock.SkillView]:
    rows = conn.execute("SELECT requires_id FROM prereqs WHERE skill_id = ? ORDER BY requires_id",
                        (skill_id,)).fetchall()
    return {r["requires_id"]: skill_view(conn, r["requires_id"]) for r in rows}


def check_unlocks(conn, now: datetime) -> list[str]:
    out = []
    locked = conn.execute(
        "SELECT st.skill_id FROM skill_state st JOIN skills s ON s.id = st.skill_id "
        "WHERE st.unlocked = 0 ORDER BY s.rowid").fetchall()
    for r in locked:
        if unlock.can_unlock(_prereq_views(conn, r["skill_id"])):
            _append(conn, now, "unlocked", None, r["skill_id"], {"reason": "mastery"})
            out.append(r["skill_id"])
    return out


def record_answer(conn: sqlite3.Connection, item_id: str, response: str, now: datetime,
                  latency_ms: int = 0) -> AnswerResult:
    item = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    answers = json.loads(item["answers"])
    correct = is_correct(response, answers)
    conn.execute("BEGIN")
    try:
        _append(conn, now, "answered", item_id, item["skill_id"],
                {"response": response, "correct": correct, "latency_ms": int(latency_ms),
                 "rating": scheduler.rating_for(correct).name.lower()})
        unlocked = check_unlocks(conn, now)
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
    return AnswerResult(correct, answers[0], item["explanation"], unlocked)


# ---------- selection ----------

def next_items(conn: sqlite3.Connection, now: datetime, limit: int = config.DEFAULT_LIMIT) -> list[str]:
    due = [r["item_id"] for r in conn.execute(
        "SELECT item_id FROM card_state WHERE due <= ? ORDER BY due, item_id", (iso(now),))]
    out = due[:limit]
    if len(out) < limit:
        new = conn.execute(
            "SELECT i.id FROM items i JOIN skills s ON s.id = i.skill_id "
            "JOIN skill_state st ON st.skill_id = s.id "
            "WHERE st.unlocked = 1 AND NOT EXISTS (SELECT 1 FROM card_state c WHERE c.item_id = i.id) "
            "ORDER BY s.rowid, i.rowid LIMIT ?", (limit - len(out),)).fetchall()
        out += [r["id"] for r in new]
    return out


class Session:
    """One study session. Initial-phase items repeat in-session until INITIAL_CORRECT."""

    def __init__(self, conn: sqlite3.Connection, clock, limit: int = config.DEFAULT_LIMIT):
        self.conn, self.clock = conn, clock
        self.started = clock.now()
        self.queue: list[str] = next_items(conn, self.started, limit)
        self.studied: set[str] = set()

    def next(self) -> sqlite3.Row | None:
        if not self.queue:
            return None
        return self.conn.execute("SELECT * FROM items WHERE id = ?", (self.queue[0],)).fetchone()

    def answer(self, response: str, latency_ms: int = 0) -> AnswerResult:
        item_id = self.queue.pop(0)
        res = record_answer(self.conn, item_id, response, self.clock.now(), latency_ms)
        self.studied.add(item_id)
        st = self.conn.execute("SELECT relearn_phase FROM card_state WHERE item_id = ?", (item_id,)).fetchone()
        if st["relearn_phase"] == "initial":
            self.queue.insert(min(config.RELEARN_GAP, len(self.queue)), item_id)
        return res


# ---------- status ----------

def status(conn: sqlite3.Connection, now: datetime) -> dict:
    local = now.astimezone()  # "today" means the learner's local calendar day
    end_of_day = datetime.combine(local.date() + timedelta(days=1), datetime.min.time(), tzinfo=local.tzinfo)
    due_now = conn.execute("SELECT COUNT(*) FROM card_state WHERE due <= ?", (iso(now),)).fetchone()[0]
    due_today = conn.execute("SELECT COUNT(*) FROM card_state WHERE due < ?", (iso(end_of_day),)).fetchone()[0]
    skills = []
    for r in conn.execute("SELECT s.id, s.title, st.p_known, st.unlocked FROM skills s "
                          "JOIN skill_state st ON st.skill_id = s.id ORDER BY s.rowid").fetchall():
        skills.append({"id": r["id"], "title": r["title"], "p_known": r["p_known"],
                       "unlocked": bool(r["unlocked"]),
                       "learned": conn.execute(
                           "SELECT COUNT(*) FROM card_state c JOIN items i ON i.id = c.item_id "
                           "WHERE i.skill_id = ? AND c.relearn_phase = 'learned'", (r["id"],)).fetchone()[0],
                       "n_items": conn.execute("SELECT COUNT(*) FROM items WHERE skill_id = ?",
                                               (r["id"],)).fetchone()[0],
                       "unmet": [] if r["unlocked"] else unlock.unmet(_prereq_views(conn, r["id"]))})
    return {"due_now": due_now, "due_today": due_today, "skills": skills}


def export_events(conn: sqlite3.Connection):
    for r in conn.execute("SELECT * FROM events ORDER BY seq"):
        yield json.dumps({"seq": r["seq"], "ts": r["ts"], "type": r["type"], "item_id": r["item_id"],
                          "skill_id": r["skill_id"], "payload": json.loads(r["payload"])})
