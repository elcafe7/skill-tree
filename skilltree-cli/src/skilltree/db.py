from __future__ import annotations
import os
import sqlite3
from importlib import resources
from pathlib import Path

DEFAULT_DB = Path.home() / ".skilltree" / "skilltree.db"


def resolve_path(path: str | None) -> Path:
    if path:
        return Path(path).expanduser()
    env = os.environ.get("SKILLTREE_DB")
    return Path(env).expanduser() if env else DEFAULT_DB


def _migrations() -> list[tuple[int, str]]:
    out = []
    for f in resources.files("skilltree").joinpath("migrations").iterdir():
        if f.name.endswith(".sql"):
            out.append((int(f.name.split("_", 1)[0]), f.read_text()))
    return sorted(out)


def connect(path: str | os.PathLike | None, migrate: bool = True) -> sqlite3.Connection:
    p = ":memory:" if str(path) == ":memory:" else str(path)
    if p != ":memory:":
        Path(p).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(p, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    if migrate:
        run_migrations(conn)
    return conn


def current_version(conn: sqlite3.Connection) -> int:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'").fetchone()
    if not row:
        return 0
    v = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]
    return v or 0


def run_migrations(conn: sqlite3.Connection) -> None:
    v = current_version(conn)
    for num, sql in _migrations():
        if num > v:
            conn.execute("BEGIN")
            try:
                for stmt in sql.split(";"):
                    if stmt.strip():
                        conn.execute(stmt)
                conn.execute("INSERT INTO schema_version(version) VALUES (?)", (num,))
                conn.execute("COMMIT")
            except Exception:
                conn.execute("ROLLBACK")
                raise
