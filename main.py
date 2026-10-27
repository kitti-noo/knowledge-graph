import argparse
from pathlib import Path

from kg import domain as dom
from kg import graph
from kg.extract import extract_triples
from kg.query import ask, grade


def paths(args):
    """--domain examples/retail-demo -> (Domain, examples/retail-demo/graph.json)."""
    d = Path(args.domain)
    return dom.load(d), d / "graph.json"


def cmd_ingest(args):
    d, graph_path = paths(args)
    g = graph.load(graph_path) if graph_path.exists() and not args.reset else None
    for f in args.files:
        triples = extract_triples(Path(f).read_text(), d)
        if d.relations:
            triples, dropped, new = dom.filter_extracted(d, triples)
            for line in dropped:
                print(f"  dropped {line}")
            if new:
                print(f"  new entities (add to entities.csv if they are real): {', '.join(sorted(new))}")
        print(f"{f}: {len(triples)} triples")
        g = graph.build(triples, g)
    graph.save(g, graph_path)
    print(f"graph: {g.number_of_nodes()} nodes, {g.number_of_edges()} edges -> {graph_path}")


def cmd_ingest_csv(args):
    d, graph_path = paths(args)
    if not (d.path / "triples.csv").exists():
        raise SystemExit(f"{d.path}/triples.csv not found (ingest-csv needs ontology.md, entities.csv, triples.csv)")
    try:
        triples = dom.load_triples(d, d.path / "triples.csv")
    except ValueError as e:
        raise SystemExit(f"fix these rows, then run again:\n{e}")
    g = graph.load(graph_path) if graph_path.exists() and not args.reset else None
    g = graph.build(triples, g)
    graph.save(g, graph_path)
    print(f"triples.csv: {len(triples)} triples")
    print(f"graph: {g.number_of_nodes()} nodes, {g.number_of_edges()} edges -> {graph_path}")


def cmd_ask(args):
    d, graph_path = paths(args)
    g = graph.load(graph_path)
    answer, seeds, facts = ask(g, args.question, args.hops, d)
    if args.verbose:
        print("seeds:", seeds)
        print("facts:\n  " + "\n  ".join(facts) + "\n")
    print(answer)


def cmd_impact(args):
    d, graph_path = paths(args)
    g = graph.load(graph_path)
    name = graph.key(d.resolve(args.system) or args.system)
    if name not in g:
        raise SystemExit(f"{args.system!r} is not in the graph")
    hit = graph.impact(g, name)
    print(f"if {g.nodes[name]['label']} goes down, {len(hit)} may be affected:")
    for n, (kind, path) in hit.items():
        print(f"  {g.nodes[n]['label']:<14} {kind:<8} {path}")


def cmd_eval(args):
    d, graph_path = paths(args)
    if not (d.path / "questions.md").exists():
        raise SystemExit(f"{d.path}/questions.md not found")
    g = graph.load(graph_path)
    questions = dom.load_questions(d)
    passed = 0
    for qid, question, expected in questions:
        answer, seeds, facts = ask(g, question, args.hops, d)
        verdict = grade(question, expected, answer)
        passed += bool(verdict.get("correct"))
        print(f"{'PASS' if verdict.get('correct') else 'FAIL'}  {qid}: {question}")
        print(f"      expected: {expected}")
        if not verdict.get("correct"):
            print(f"      missing:  {verdict.get('missing')}")
            print(f"      seeds:    {seeds}")
            if args.verbose:
                print("      answer:   " + answer.replace("\n", "\n                "))
    print(f"\n{passed}/{len(questions)} passed")


def cmd_viz(args):
    d, graph_path = paths(args)
    out = Path(args.out) if args.out else graph_path.with_suffix(".html")
    graph.visualize(graph.load(graph_path), out)
    print(f"open {out}")


def cmd_stats(args):
    d, graph_path = paths(args)
    g = graph.load(graph_path)
    print(f"{g.number_of_nodes()} nodes, {g.number_of_edges()} edges")
    for n, deg in sorted(g.degree, key=lambda x: -x[1])[:10]:
        print(f"  {deg:3}  {g.nodes[n]['label']} ({g.nodes[n]['type']})")
    if deg_zero := [g.nodes[n]["label"] for n, deg in g.degree if deg == 0]:
        print(f"  not connected: {', '.join(deg_zero)}")


common = argparse.ArgumentParser(add_help=False)
common.add_argument("--domain", default="examples/thai-tourism", help="domain folder (default: %(default)s)")

p = argparse.ArgumentParser()
sub = p.add_subparsers(required=True)

s = sub.add_parser("ingest", parents=[common], help="extract triples from text files into the graph (LLM)")
s.add_argument("files", nargs="+")
s.add_argument("--reset", action="store_true")
s.set_defaults(fn=cmd_ingest)

s = sub.add_parser("ingest-csv", parents=[common], help="load <domain>/triples.csv into the graph (no LLM)")
s.add_argument("--reset", action="store_true")
s.set_defaults(fn=cmd_ingest_csv)

s = sub.add_parser("ask", parents=[common], help="answer a question from the graph")
s.add_argument("question")
s.add_argument("--hops", type=int, default=2)
s.add_argument("-v", "--verbose", action="store_true")
s.set_defaults(fn=cmd_ask)

s = sub.add_parser("impact", parents=[common], help="what breaks if this system goes down (no LLM)")
s.add_argument("system")
s.set_defaults(fn=cmd_impact)

s = sub.add_parser("eval", parents=[common], help="ask every question in <domain>/questions.md and grade it")
s.add_argument("--hops", type=int, default=2)
s.add_argument("-v", "--verbose", action="store_true")
s.set_defaults(fn=cmd_eval)

s = sub.add_parser("viz", parents=[common], help="render graph to interactive HTML")
s.add_argument("--out")
s.set_defaults(fn=cmd_viz)

s = sub.add_parser("stats", parents=[common], help="most connected entities")
s.set_defaults(fn=cmd_stats)

args = p.parse_args()
args.fn(args)
