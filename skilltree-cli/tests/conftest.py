import sys
from pathlib import Path
import pytest
from skilltree import db, engine
from skilltree.clock import FakeClock
from skilltree.yaml_import import load_file

FIXTURE = Path(__file__).parent / "fixtures" / "tree.yaml"
sys.path.insert(0, str(Path(__file__).parent))


@pytest.fixture
def clock():
    return FakeClock()


@pytest.fixture
def conn(tmp_path):
    c = db.connect(tmp_path / "t.db")
    yield c
    c.close()


@pytest.fixture
def loaded(conn, clock):
    engine.import_tree(conn, load_file(FIXTURE), "tree.yaml", clock.now())
    return conn


def dump(conn, table):
    return [tuple(r) for r in conn.execute(f"SELECT * FROM {table} ORDER BY 1")]
