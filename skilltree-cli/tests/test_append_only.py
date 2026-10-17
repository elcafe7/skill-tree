import re
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src" / "skilltree"


def test_no_update_or_delete_on_events():
    pat = re.compile(r"\b(UPDATE\s+events|DELETE\s+FROM\s+events|REPLACE\s+INTO\s+events|DROP\s+TABLE\s+events)\b", re.I)
    hits = [f"{p.name}:{i}" for p in SRC.rglob("*.py") for i, line in enumerate(p.read_text().splitlines(), 1)
            if pat.search(line)]
    assert hits == []
