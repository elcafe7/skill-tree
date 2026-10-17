from . import config


def update(p: float, correct: bool, guess: float = config.P_GUESS, slip: float = config.P_SLIP,
           transit: float = config.P_TRANSIT) -> float:
    if correct:
        post = p * (1 - slip) / (p * (1 - slip) + (1 - p) * guess)
    else:
        post = p * slip / (p * slip + (1 - p) * (1 - guess))
    return post + (1 - post) * transit
