"""Step 3: GraphRAG. Question -> seed entities -> k-hop subgraph -> answer.

Compare with vector RAG: retrieval here follows relationships, so multi-hop
questions ("where did the husband of X's collaborator study?") become possible.
"""

import networkx as nx

from .graph import key, subgraph_facts
from .llm import chat, chat_json


def find_seeds(g: nx.MultiDiGraph, question: str, domain=None) -> list[str]:
    labels = [d["label"] for _, d in g.nodes(data=True)]
    if domain and domain.entities:  # let the LLM see nicknames too ("ระบบคูปอง" -> Coupon Engine)
        labels = [
            f"{l} (aka {a.replace('|', ', ')})" if (a := domain.entities.get(l, {}).get("aliases")) else l
            for l in labels
        ]
    data = chat_json(
        f"Question: {question}\n\nKnown entities: {labels}\n\n"
        'Return JSON {"entities": [...]} with the known entities the question is about. '
        "Use names exactly as listed, without the (aka ...) part."
    )
    names = data.get("entities", [])
    if domain:
        names = [domain.resolve(n) or n for n in names]
    return [key(e) for e in names if key(e) in g]


def ask(g: nx.MultiDiGraph, question: str, hops: int = 2, domain=None) -> tuple[str, list[str], list[str]]:
    seeds = find_seeds(g, question, domain)
    facts = subgraph_facts(g, seeds, hops)
    if not facts:
        return "No relevant entities found in the graph.", seeds, facts
    meanings = ""
    if domain and domain.meanings:  # e.g. VIA = "sent through this channel", so "ช่องทาง" maps to VIA
        meanings = "Relation meanings:\n" + "\n".join(f"  {r}: {m}" for r, m in domain.meanings.items()) + "\n\n"
    answer = chat(
        "Answer the question using ONLY these facts from a knowledge graph. "
        "Explain the path of relations you followed. If the facts are insufficient, say so.\n\n"
        + meanings + "Facts:\n" + "\n".join(facts) + f"\n\nQuestion: {question}"
    )
    return answer, seeds, facts


def grade(question: str, expected: str, answer: str) -> dict:
    """LLM-as-judge for `eval`: does the answer contain what the expected answer says?"""
    return chat_json(
        f"Question: {question}\nExpected answer: {expected}\nGiven answer: {answer}\n\n"
        "Does the given answer contain the key facts of the expected answer? Extra correct detail is fine. "
        'Return JSON {"correct": true|false, "missing": "what is missing or wrong, empty if correct"}'
    )
