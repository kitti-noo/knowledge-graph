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
            attrs = {k: t[k] for k in ("source_chunk", "note", "source") if t.get(k) not in (None, "")}
            g.add_edge(s, o, relation=t["relation"], **attrs)
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
        note = f"  # {d['note']}" if d.get("note") else ""
        facts.append(f"({g.nodes[u]['label']}) -[{d['relation']}]-> ({g.nodes[v]['label']}){note}")
    return sorted(set(facts))


def impact(g: nx.MultiDiGraph, start: str) -> dict[str, str]:
    """Everything that breaks, directly or in a chain, when `start` goes down. Pure graph walk, no LLM.

    X down hurts Y when: X -SENDS_TO-> Y, Y -DEPENDS_ON-> X,
    or X -PRODUCES-> data <-CONSUMES- Y. Returns {node: ("direct" | "chain N", path from start)}.
    Chains are worst case: a person still judges whether the break really propagates.
    """
    label = lambda n: g.nodes[n]["label"]

    def hurt_by(x):
        # Most explicit relation first, so the reported path is the clearest one.
        for y, _, d in g.in_edges(x, data=True):
            if d["relation"] == "DEPENDS_ON":
                yield y, f"<-[DEPENDS_ON]- ({label(y)})"
        for _, y, d in g.out_edges(x, data=True):
            if d["relation"] == "SENDS_TO":
                yield y, f"-[SENDS_TO]-> ({label(y)})"
        for _, data, d in g.out_edges(x, data=True):
            if d["relation"] == "PRODUCES":
                for c, _, d2 in g.in_edges(data, data=True):
                    if d2["relation"] == "CONSUMES" and c != x:
                        yield c, f"-[PRODUCES]-> ({label(data)}) <-[CONSUMES]- ({label(c)})"

    paths, depth, queue = {start: f"({label(start)})"}, {start: 0}, [start]
    while queue:
        x = queue.pop(0)
        for y, step in hurt_by(x):
            if y not in paths:
                paths[y], depth[y] = f"{paths[x]} {step}", depth[x] + 1
                queue.append(y)
    del paths[start]
    return {n: ("direct" if depth[n] == 1 else f"chain {depth[n]}", p) for n, p in paths.items()}


def visualize(g: nx.MultiDiGraph, path: Path) -> None:
    from pyvis.network import Network

    net = Network(height="800px", width="100%", directed=True, cdn_resources="remote")
    for n, d in g.nodes(data=True):
        net.add_node(n, label=d["label"], title=d["type"], group=d["type"])
    for u, v, d in g.edges(data=True):
        net.add_edge(u, v, label=d["relation"], title=" | ".join(filter(None, [d.get("note"), d.get("source")])) or None)
    net.write_html(str(path), notebook=False)
