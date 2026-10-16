def normalize(s: str) -> str:
    return " ".join(s.split()).casefold()


def is_correct(response: str, answers: list[str]) -> bool:
    r = normalize(response)
    return any(r == normalize(a) for a in answers)
