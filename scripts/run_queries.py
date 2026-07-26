"""Run the README showcase queries against a loaded legal-judgments graph."""

import sys
sys.path.insert(0, ".")
from samyama import SamyamaClient
from etl.loader import load_legal_judgments

GRAPH = "legal-judgments"


def q(client, cypher):
    r = client.query_readonly(cypher, GRAPH)
    return [dict(zip(r.columns, row)) for row in r.records]


def run_all(client):
    print("=" * 70)
    print("LEGAL-JUDGMENTS-KG SHOWCASE QUERIES")
    print("=" * 70)

    print("\n## Graph Statistics\n")
    for label in ["Case", "Judge", "Party", "Act", "Topic"]:
        rows = q(client, f"MATCH (n:{label}) RETURN count(n) AS c")
        print(f"  {label:8s} {rows[0]['c']:>6,}")
    total_nodes = q(client, "MATCH (n) RETURN count(n) AS c")[0]["c"]
    total_edges = q(client, "MATCH ()-[r]->() RETURN count(r) AS c")[0]["c"]
    print(f"\n  {'Total nodes':12s} {total_nodes:>6,}")
    print(f"  {'Total edges':12s} {total_edges:>6,}")

    print("\n## Most productive judges\n")
    for r in q(client, """
        MATCH (j:Judge)-[:DECIDED]->(c:Case)
        RETURN j.name AS judge, count(DISTINCT c) AS cases
        ORDER BY cases DESC LIMIT 5
    """):
        print(f"  {r['judge']:24s} {r['cases']}")

    print("\n## Most-cited legal sections\n")
    for r in q(client, """
        MATCH (c:Case)-[rel:CITES]->(a:Act)
        RETURN a.name AS act, rel.section AS section, count(DISTINCT c) AS cases
        ORDER BY cases DESC LIMIT 5
    """):
        print(f"  {r['act']} §{r['section']}: {r['cases']}")

    print("\n## Judges who most often sit together\n")
    for r in q(client, """
        MATCH (j1:Judge)-[:DECIDED]->(c:Case)<-[:DECIDED]-(j2:Judge)
        WHERE j1.name < j2.name
        RETURN j1.name AS a, j2.name AS b, count(DISTINCT c) AS together
        ORDER BY together DESC LIMIT 5
    """):
        print(f"  {r['a']} & {r['b']}: {r['together']}")

    print("\n## Laws spanning the widest range of topics\n")
    for r in q(client, """
        MATCH (a:Act)<-[:CITES]-(c:Case)-[:ABOUT]->(t:Topic)
        RETURN a.name AS act, count(DISTINCT t.category) AS breadth, count(DISTINCT c) AS cases
        ORDER BY breadth DESC, cases DESC LIMIT 5
    """):
        print(f"  {r['act']}: {r['breadth']} categories / {r['cases']} cases")


if __name__ == "__main__":
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "data"
    print(f"Loading data from {data_dir}...", flush=True)
    c = SamyamaClient.embedded()
    load_legal_judgments(c, data_dir=data_dir)
    run_all(c)
