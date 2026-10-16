from typer.testing import CliRunner
from skilltree.cli import app
from conftest import FIXTURE


def test_end_to_end(tmp_path):
    r = CliRunner()
    db = str(tmp_path / "x.db")
    assert r.invoke(app, ["--db", db, "init"]).exit_code == 0
    assert r.invoke(app, ["--db", db, "init"]).exit_code == 0
    res = r.invoke(app, ["--db", db, "import", str(FIXTURE)])
    assert res.exit_code == 0 and "4 skills, 12 items" in res.output
    res = r.invoke(app, ["--db", db, "study", "--limit", "2"], input="5\nnope\n\n:q\n")
    assert res.exit_code == 0, res.output
    assert "Correct." in res.output and "Answer: 8" in res.output and "Doubles" in res.output
    res = r.invoke(app, ["--db", db, "status"])
    assert "needs A" in res.output and "p_known=" in res.output
    assert r.invoke(app, ["--db", db, "rebuild"]).exit_code == 0
    res = r.invoke(app, ["--db", db, "export"])
    assert res.output.count('"type": "answered"') == 2
