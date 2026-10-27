"""Step 1: text -> (subject, relation, object) triples.

In RAG you chunk and embed. Here you chunk and *extract structure*.
"""

from .llm import chat_json

SYSTEM = """You extract a knowledge graph from text.
Return JSON: {"triples": [{"subject": str, "subject_type": str,
"relation": str, "object": str, "object_type": str}]}
Rules:
- Entities are canonical names (e.g. "Marie Curie", not "she" / "Curie").
- Keep entity names in the language of the text (Thai stays Thai). Use the fullest name given as canonical.
- Types are short labels: Person, Organization, Place, Concept, Award, Event, Work, Date.
- Relations are UPPER_SNAKE_CASE verbs: WORKED_AT, MARRIED_TO, DISCOVERED, BORN_IN.
- Only facts stated in the text. No guesses."""


def system_prompt(domain=None) -> str:
    """With a domain, lock types/relations to its ontology and reuse its official names."""
    if domain is None or not domain.relations:
        return SYSTEM
    relations = "\n".join(f"  - {r} ({a} -> {b})" for r, (a, b) in domain.relations.items())
    known = "\n".join(
        f"  - {name} ({e['type']})" + (f", also called: {e['aliases'].replace('|', ', ')}" if e.get("aliases") else "")
        for name, e in domain.entities.items()
    )
    return f"""{SYSTEM}

This domain has a fixed ontology. It overrides the type and relation examples above.
- Types: {", ".join(sorted(domain.types))}
- Relations (subject type -> object type):
{relations}
Known entities. When the text uses a name or nickname listed here, output the official name:
{known}
A new entity not listed above is allowed only if the text clearly names it."""


def chunk(text: str, max_chars: int = 1500) -> list[str]:
    chunks, buf = [], ""
    for para in text.split("\n\n"):
        if len(buf) + len(para) > max_chars and buf:
            chunks.append(buf)
            buf = ""
        buf += para + "\n\n"
    if buf.strip():
        chunks.append(buf)
    return chunks


def extract_triples(text: str, domain=None) -> list[dict]:
    triples = []
    system = system_prompt(domain)
    for i, c in enumerate(chunk(text)):
        data = chat_json(f"Text:\n{c}", system=system)
        found = [t for t in data.get("triples", []) if t.get("subject") and t.get("object")]
        for t in found:
            t["source_chunk"] = i
        triples.extend(found)
    return triples
