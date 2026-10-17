from __future__ import annotations
import json
from dataclasses import dataclass, field
from pathlib import Path
import yaml


class ImportErrorTree(ValueError):
    pass


@dataclass
class Item:
    id: str
    prompt: str
    answers: list[str]
    explanation: str
    worked_example: str | None = None


@dataclass
class Skill:
    id: str
    title: str
    requires: list[str]
    parent_id: str | None = None
    items: list[Item] = field(default_factory=list)


def parse(text: str) -> list[Skill]:
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as e:
        raise ImportErrorTree(f"invalid YAML: {e}") from e
    if not isinstance(data, dict) or not isinstance(data.get("skills"), list):
        raise ImportErrorTree("top level must be a mapping with a 'skills' list")
    skills, seen = [], set()
    for s in data["skills"]:
        if not isinstance(s, dict) or "id" not in s:
            raise ImportErrorTree("every skill needs an 'id'")
        sid = str(s["id"])
        if sid in seen:
            raise ImportErrorTree(f"duplicate id: {sid}")
        seen.add(sid)
        items = []
        for it in s.get("items") or []:
            iid = str(it.get("id", ""))
            if not iid:
                raise ImportErrorTree(f"item without id in skill {sid}")
            if iid in seen:
                raise ImportErrorTree(f"duplicate id: {iid}")
            seen.add(iid)
            answers = it.get("answers") or []
            if not isinstance(answers, list) or not [a for a in answers if str(a).strip()]:
                raise ImportErrorTree(f"item {iid} needs at least one answer")
            if not str(it.get("explanation") or "").strip():
                raise ImportErrorTree(f"item {iid} needs an explanation")
            if not str(it.get("prompt") or "").strip():
                raise ImportErrorTree(f"item {iid} needs a prompt")
            items.append(Item(iid, str(it["prompt"]), [str(a) for a in answers],
                              str(it["explanation"]), it.get("worked_example")))
        skills.append(Skill(sid, str(s.get("title") or sid), [str(r) for r in s.get("requires") or []],
                            s.get("parent_id"), items))
    validate(skills)
    return skills


def validate(skills: list[Skill]) -> None:
    ids = {s.id for s in skills}
    for s in skills:
        for r in s.requires:
            if r not in ids:
                raise ImportErrorTree(f"skill {s.id} requires unknown id: {r}")
        if s.parent_id is not None and s.parent_id not in ids:
            raise ImportErrorTree(f"skill {s.id} has unknown parent_id: {s.parent_id}")
    graph = {s.id: s.requires for s in skills}
    state: dict[str, int] = {}

    def visit(n: str, path: list[str]) -> None:
        if state.get(n) == 1:
            cyc = path[path.index(n):] + [n]
            raise ImportErrorTree("cycle: " + " -> ".join(cyc))
        if state.get(n) == 2:
            return
        state[n] = 1
        for m in graph[n]:
            visit(m, path + [n])
        state[n] = 2

    for n in graph:
        visit(n, [])


def load_file(path: str | Path) -> list[Skill]:
    return parse(Path(path).read_text())


def summary(skills: list[Skill]) -> tuple[int, int]:
    return len(skills), sum(len(s.items) for s in skills)


def item_row(skill_id: str, it: Item) -> tuple:
    return (it.id, skill_id, "recall", it.prompt, json.dumps(it.answers), it.explanation, it.worked_example)
