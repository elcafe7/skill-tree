from skilltree import bkt, config


def test_defaults():
    assert (config.P_INIT, config.P_TRANSIT, config.P_GUESS, config.P_SLIP) == (0.1, 0.15, 0.05, 0.1)


def test_hand_computed_sequences():
    # correct from 0.1: post = .09/(.09+.045) = 2/3 ; p = 2/3 + (1/3)(.15) = 0.7166666...
    p1 = bkt.update(0.1, True)
    assert abs(p1 - (2 / 3 + (1 / 3) * 0.15)) < 1e-9
    assert abs(p1 - 0.71666666666666667) < 1e-9
    # wrong from 0.1: post = .01/(.01+.855) = 0.011560693641618497 ; p = post + (1-post)*.15
    post = 0.01 / (0.01 + 0.9 * 0.95)
    assert abs(bkt.update(0.1, False) - (post + (1 - post) * 0.15)) < 1e-9
    assert abs(bkt.update(0.1, False) - 0.15982658959537572) < 1e-9
    # correct, correct
    p = bkt.update(bkt.update(0.1, True), True)
    q = 0.7166666666666667
    post = q * 0.9 / (q * 0.9 + (1 - q) * 0.05)
    assert abs(p - (post + (1 - post) * 0.15)) < 1e-9
    assert abs(p - 0.98173198482933) < 1e-9
