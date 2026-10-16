"""Typer CLI. I/O only; all rules live in the core modules."""
from __future__ import annotations
import sys
import time
from pathlib import Path
from typing import Optional

import typer

from . import config, db, engine
from .clock import SystemClock
from .yaml_import import ImportErrorTree, load_file

app = typer.Typer(add_completion=False, help="Single-user offline skill-tree learning CLI.")
_state = {"db": None}
clock = SystemClock()


@app.callback()
def main(db_path: Optional[str] = typer.Option(None, "--db", help="SQLite file (or set SKILLTREE_DB).")):
    _state["db"] = db_path


def _conn():
    return db.connect(db.resolve_path(_state["db"]))


@app.command()
def init():
    """Create the database and run migrations (safe to re-run)."""
    _conn().close()
    typer.echo("Database ready.")


@app.command("import")
def import_(path: Path):
    """Validate and import a YAML skill tree."""
    try:
        skills = load_file(path)
    except (ImportErrorTree, OSError) as e:
        typer.echo(f"Import failed: {e}", err=True)
        raise typer.Exit(1)
    conn = _conn()
    n_sk, n_it = engine.import_tree(conn, skills, path.name, clock.now())
    typer.echo(f"Imported {n_sk} skills, {n_it} items.")


def _read(prompt: str) -> Optional[str]:
    typer.echo(prompt, nl=False)
    line = sys.stdin.readline()
    if line == "":
        return None
    return line.rstrip("\n")


@app.command()
def study(limit: int = typer.Option(config.DEFAULT_LIMIT, "--limit", min=1)):
    """Interactive study loop. Ctrl-D or :q ends the session."""
    conn = _conn()
    s = engine.Session(conn, clock, limit)
    answered = 0
    while (item := s.next()) is not None:
        typer.echo(f"\n[{item['skill_id']}] {item['prompt']}")
        t0 = time.monotonic()
        resp = _read("> ")
        if resp is None or resp.strip() == ":q":
            break
        res = s.answer(resp, int((time.monotonic() - t0) * 1000))
        answered += 1
        if res.correct:
            typer.echo("Correct.")
            typer.echo(res.explanation)
        else:
            typer.echo(f"Not quite. Answer: {res.correct_answer}")
            typer.echo(res.explanation)
            if _read("(press Enter to continue) ") is None:
                for u in res.unlocked:
                    typer.echo(f"Unlocked: {u}")
                break
        for u in res.unlocked:
            typer.echo(f"Unlocked: {u}")
    typer.echo(f"\nSession over. {answered} answers recorded.")


@app.command()
def status():
    """Due counts and per-skill mastery and lock state."""
    st = engine.status(_conn(), clock.now())
    typer.echo(f"Due now: {st['due_now']}   Due today: {st['due_today']}")
    for sk in st["skills"]:
        state = "unlocked" if sk["unlocked"] else "locked"
        typer.echo(f"  {sk['id']:<20} p_known={sk['p_known']:.2f}  {state}")
        for pid, why in sk["unmet"]:
            typer.echo(f"      needs {pid}: {why}")


@app.command()
def rebuild():
    """Drop derived tables and replay events."""
    engine.rebuild(_conn())
    typer.echo("Rebuilt derived state from events.")


@app.command()
def export(path: Optional[Path] = typer.Argument(None)):
    """Write events as JSONL (default stdout)."""
    lines = engine.export_events(_conn())
    if path is None:
        for l in lines:
            typer.echo(l)
    else:
        with open(path, "w") as f:
            for l in lines:
                f.write(l + "\n")


if __name__ == "__main__":
    app()
