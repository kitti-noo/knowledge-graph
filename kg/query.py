"""Step 3: GraphRAG. Question -> seed entities -> k-hop subgraph -> answer.

Compare with vector RAG: retrieval here follows relationships, so multi-hop
questions ("where did the husband of X's collaborator study?") become possible.
"""

import networkx as nx

from .graph import key, subgraph_facts
from .llm import chat, chat_json


def find_seeds(g: nx.MultiDiGraph, question: str) -> list[str]:
    labels = [d["label"] for _, d in g.nodes(data=True)]
    data = chat_json(
        f"Question: {question}\n\nKnown entities: {labels}\n\n"
        'Return JSON {"entities": [...]} with the known entities the question is about. '
        "Use names exactly as listed."
    )
    return [key(e) for e in data.get("entities", []) if key(e) in g]


def ask(g: nx.MultiDiGraph, question: str, hops: int = 2) -> tuple[str, list[str], list[str]]:
    seeds = find_seeds(g, question)
    facts = subgraph_facts(g, seeds, hops)
    if not facts:
        return "No relevant entities found in the graph.", seeds, facts
    answer = chat(
        "Answer the question using ONLY these facts from a knowledge graph. "
        "Explain the path of relations you followed. If the facts are insufficient, say so.\n\n"
        "Facts:\n" + "\n".join(facts) + f"\n\nQuestion: {question}"
    )
    return answer, seeds, facts
