import argparse
from pathlib import Path

from kg import graph
from kg.extract import extract_triples
from kg.query import ask

GRAPH_PATH = Path("data/graph.json")


def cmd_ingest(args):
    g = graph.load(GRAPH_PATH) if GRAPH_PATH.exists() and not args.reset else None
    for f in args.files:
        triples = extract_triples(Path(f).read_text())
        print(f"{f}: {len(triples)} triples")
        g = graph.build(triples, g)
    graph.save(g, GRAPH_PATH)
    print(f"graph: {g.number_of_nodes()} nodes, {g.number_of_edges()} edges -> {GRAPH_PATH}")


def cmd_ask(args):
    g = graph.load(GRAPH_PATH)
    answer, seeds, facts = ask(g, args.question, args.hops)
    if args.verbose:
        print("seeds:", seeds)
        print("facts:\n  " + "\n  ".join(facts) + "\n")
    print(answer)


def cmd_viz(args):
    out = Path(args.out)
    graph.visualize(graph.load(GRAPH_PATH), out)
    print(f"open {out}")


def cmd_stats(args):
    g = graph.load(GRAPH_PATH)
    print(f"{g.number_of_nodes()} nodes, {g.number_of_edges()} edges")
    for n, deg in sorted(g.degree, key=lambda x: -x[1])[:10]:
        print(f"  {deg:3}  {g.nodes[n]['label']} ({g.nodes[n]['type']})")


p = argparse.ArgumentParser()
sub = p.add_subparsers(required=True)

s = sub.add_parser("ingest", help="extract triples from text files into the graph")
s.add_argument("files", nargs="+")
s.add_argument("--reset", action="store_true")
s.set_defaults(fn=cmd_ingest)

s = sub.add_parser("ask", help="answer a question from the graph")
s.add_argument("question")
s.add_argument("--hops", type=int, default=2)
s.add_argument("-v", "--verbose", action="store_true")
s.set_defaults(fn=cmd_ask)

s = sub.add_parser("viz", help="render graph to interactive HTML")
s.add_argument("--out", default="data/graph.html")
s.set_defaults(fn=cmd_viz)

s = sub.add_parser("stats", help="most connected entities")
s.set_defaults(fn=cmd_stats)

args = p.parse_args()
args.fn(args)
