"""Step 1: text -> (subject, relation, object) triples.

In RAG you chunk and embed. Here you chunk and *extract structure*.
"""

from .llm import chat_json

SYSTEM = """You extract a knowledge graph from text.
Return JSON: {"triples": [{"subject": str, "subject_type": str,
"relation": str, "object": str, "object_type": str}]}
Rules:
- Entities are canonical names (e.g. "Marie Curie", not "she" / "Curie").
- Types are short labels: Person, Organization, Place, Concept, Award, Event, Work, Date.
- Relations are UPPER_SNAKE_CASE verbs: WORKED_AT, MARRIED_TO, DISCOVERED, BORN_IN.
- Only facts stated in the text. No guesses."""


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


def extract_triples(text: str) -> list[dict]:
    triples = []
    for i, c in enumerate(chunk(text)):
        data = chat_json(f"Text:\n{c}", system=SYSTEM)
        found = [t for t in data.get("triples", []) if t.get("subject") and t.get("object")]
        for t in found:
            t["source_chunk"] = i
        triples.extend(found)
    return triples
