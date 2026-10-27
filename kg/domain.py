"""Domain folder: ontology.md + entities.csv + triples.csv (+ questions.md).

Structured data goes straight into the graph; only free text needs the LLM.
The ontology and the entity list are the rules both paths must follow.
"""

import csv
import re
from dataclasses import dataclass, field
from pathlib import Path

from .graph import key


@dataclass
class Domain:
    path: Path
    types: set[str] = field(default_factory=set)
    relations: dict[str, tuple[str, str]] = field(default_factory=dict)  # relation -> (from type, to type)
    meanings: dict[str, str] = field(default_factory=dict)  # relation -> what it means, from ontology.md
    entities: dict[str, dict] = field(default_factory=dict)  # official name -> entities.csv row
    aliases: dict[str, str] = field(default_factory=dict)  # key(name or alias) -> official name

    def resolve(self, name: str) -> str | None:
        return self.aliases.get(key(name))

    def type_of(self, name: str) -> str:
        return self.entities[name]["type"]


def load(path: Path) -> Domain:
    d = Domain(path)
    if (path / "ontology.md").exists():
        _load_ontology(d, (path / "ontology.md").read_text())
    if (path / "entities.csv").exists():
        _load_entities(d, path / "entities.csv")
    return d


def _load_ontology(d: Domain, text: str) -> None:
    # Reads the first column of the tables under "## Entity types" and "## Relations".
    section = None
    for line in text.splitlines():
        if line.startswith("## "):
            title = line.lower()
            section = "types" if "type" in title else "relations" if "relation" in title else None
            continue
        m = re.match(r"\|\s*([A-Z][A-Za-z_]*)\s*\|\s*([^|]*)\|\s*([^|]*)\|", line)
        if not m or section is None or m.group(1) in ("Type", "Relation"):
            continue
        if section == "types":
            d.types.add(m.group(1))
        else:
            ends = re.findall(r"[A-Za-z]+", m.group(2))
            d.relations[m.group(1)] = (ends[0], ends[1]) if len(ends) == 2 else ("", "")
            d.meanings[m.group(1)] = m.group(3).strip()


def _rows(path: Path):
    # utf-8-sig: Excel's "CSV UTF-8" export starts with a BOM.
    with open(path, newline="", encoding="utf-8-sig") as f:
        for i, row in enumerate(csv.DictReader(f), start=2):
            yield i, {k: (v or "").strip() for k, v in row.items()}


def _load_entities(d: Domain, path: Path) -> None:
    errors = []
    for i, row in _rows(path):
        name = row["name"]
        if d.types and row["type"] not in d.types:
            errors.append(f"entities.csv row {i}: type {row['type']!r} is not in ontology.md")
        for alias in [name, *row.get("aliases", "").split("|")]:
            if not alias:
                continue
            if key(alias) in d.aliases and d.aliases[key(alias)] != name:
                errors.append(f"entities.csv row {i}: {alias!r} already means {d.aliases[key(alias)]!r}")
            d.aliases[key(alias)] = name
        d.entities[name] = row
    if errors:
        raise ValueError("\n".join(errors))


def _check(d: Domain, s: str, rel: str, o: str) -> str | None:
    """Why a triple breaks the ontology, or None if it is fine."""
    if rel not in d.relations:
        return f"relation {rel!r} is not in ontology.md"
    want_s, want_o = d.relations[rel]
    got_s, got_o = d.type_of(s), d.type_of(o)
    if want_s and (got_s, got_o) != (want_s, want_o):
        return f"{rel} must go {want_s} -> {want_o}, got {s} ({got_s}) -> {o} ({got_o}); reversed?"
    return None


def load_triples(d: Domain, path: Path) -> list[dict]:
    """triples.csv -> triples. Fails with every bad row listed, so the CSV can be fixed in one go."""
    triples, errors = [], []
    for i, row in _rows(path):
        s, o, rel = d.resolve(row["subject"]), d.resolve(row["object"]), row["relation"]
        for col, name in (("subject", s), ("object", o)):
            if name is None:
                errors.append(f"triples.csv row {i}: {col} {row[col]!r} is not in entities.csv")
        if s is None or o is None:
            continue
        if problem := _check(d, s, rel, o):
            errors.append(f"triples.csv row {i}: {problem}")
            continue
        triples.append({
            "subject": s, "subject_type": d.type_of(s), "relation": rel,
            "object": o, "object_type": d.type_of(o),
            "note": row.get("note", ""), "source": row.get("source") or path.name,
        })
    if errors:
        raise ValueError("\n".join(errors))
    return triples


def filter_extracted(d: Domain, triples: list[dict]) -> tuple[list[dict], list[str], set[str]]:
    """LLM triples -> (kept, dropped reasons, new entity names).

    Nicknames are mapped to official names. Entities not in entities.csv are kept
    (so documents can add knowledge) but reported, so a person decides whether to add them.
    """
    kept, dropped, new = [], [], set()
    for t in triples:
        for side in ("subject", "object"):
            official = d.resolve(t[side])
            if official:
                t[side], t[f"{side}_type"] = official, d.type_of(official)
            else:
                new.add(f"{t[side]} ({t.get(f'{side}_type', '?')})")
        line = f"({t['subject']}) -[{t['relation']}]-> ({t['object']})"
        if t["relation"] not in d.relations:
            dropped.append(f"{line}: relation not in ontology")
        elif t.get("subject_type") not in d.types or t.get("object_type") not in d.types:
            dropped.append(f"{line}: type not in ontology")
        elif d.relations[t["relation"]][0] and (t["subject_type"], t["object_type"]) != d.relations[t["relation"]]:
            dropped.append(f"{line}: wrong direction/types for {t['relation']}")
        else:
            kept.append(t)
    return kept, dropped, new


def load_questions(d: Domain) -> list[tuple[str, str, str]]:
    """questions.md -> [(id, question, expected answer)]."""
    text = (d.path / "questions.md").read_text()
    return re.findall(r"^##\s*(Q\d+):\s*(.+?)\s*\n+คำตอบ:\s*(.+?)\s*$", text, re.M)
