"""Step 2: triples -> graph. Stored as a NetworkX MultiDiGraph, persisted to JSON."""

import json
from pathlib import Path

import networkx as nx


def key(name: str) -> str:
    # Naive entity resolution: "Marie Curie" == "marie curie". Improving this is half the job.
    return " ".join(name.lower().split())


def build(triples: list[dict], g: nx.MultiDiGraph | None = None) -> nx.MultiDiGraph:
    g = g if g is not None else nx.MultiDiGraph()
    for t in triples:
        s, o = key(t["subject"]), key(t["object"])
        g.add_node(s, label=t["subject"], type=t.get("subject_type", "Entity"))
        g.add_node(o, label=t["object"], type=t.get("object_type", "Entity"))
        if not any(d["relation"] == t["relation"] for d in g.get_edge_data(s, o, default={}).values()):
            g.add_edge(s, o, relation=t["relation"], source_chunk=t.get("source_chunk"))
    return g


def save(g: nx.MultiDiGraph, path: Path) -> None:
    path.write_text(json.dumps(nx.node_link_data(g, edges="edges"), ensure_ascii=False, indent=2))


def load(path: Path) -> nx.MultiDiGraph:
    return nx.node_link_graph(json.loads(path.read_text()), directed=True, multigraph=True, edges="edges")


def subgraph_facts(g: nx.MultiDiGraph, seeds: list[str], hops: int = 2) -> list[str]:
    """k-hop neighbourhood around the seed entities, rendered as fact lines for the LLM."""
    undirected = g.to_undirected(as_view=True)
    nodes = set()
    for s in seeds:
        if s in g:
            nodes |= set(nx.ego_graph(undirected, s, radius=hops))
    facts = []
    for u, v, d in g.subgraph(nodes).edges(data=True):
        facts.append(f"({g.nodes[u]['label']}) -[{d['relation']}]-> ({g.nodes[v]['label']})")
    return sorted(set(facts))


def visualize(g: nx.MultiDiGraph, path: Path) -> None:
    from pyvis.network import Network

    net = Network(height="800px", width="100%", directed=True, cdn_resources="remote")
    for n, d in g.nodes(data=True):
        net.add_node(n, label=d["label"], title=d["type"], group=d["type"])
    for u, v, d in g.edges(data=True):
        net.add_edge(u, v, label=d["relation"])
    net.write_html(str(path), notebook=False)
