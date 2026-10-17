from skilltree.grading import is_correct, normalize


def test_normalize():
    assert normalize("  Hello   World \n") == "hello world"
    assert normalize("STRASSE") == normalize("straße")


def test_alternates_and_exact():
    assert is_correct("0.75", ["3/4", "0.75"])
    assert is_correct(" 3/4 ", ["3/4", "0.75"])
    assert is_correct("FIVE", ["5", "five"])
    assert not is_correct("3 / 4", ["3/4"])
    assert not is_correct("fiv", ["five"])
