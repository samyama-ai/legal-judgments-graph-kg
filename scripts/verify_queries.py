"""Verify graph statistics and the reference demo's published numbers after a full load.

Checks the figures we claim: 4,462 nodes / 8,363 edges, Dipak Misra = 104,
IPC 302 = 57, Constitution Article 32 = 36.
"""
import sys
sys.path.insert(0, ".")
from samyama import SamyamaClient
from etl.loader import load_legal_judgments

GRAPH = "legal-judgments"


def q(client, cypher):
    r = client.query_readonly(cypher, GRAPH)
    return [dict(zip(r.columns, row)) for row in r.records]


def verify(client):
    print("=" * 60, flush=True)
    print("VERIFYING LEGAL-JUDGMENTS-KG NUMBERS", flush=True)
    print("=" * 60, flush=True)

    print("\n--- GRAPH STATS ---", flush=True)
    for label in ["Case", "Judge", "Party", "Act", "Topic"]:
        c = q(client, f"MATCH (n:{label}) RETURN count(n) AS c")[0]["c"]
        print(f"  {label}: {c:,}", flush=True)
    nodes = q(client, "MATCH (n) RETURN count(n) AS c")[0]["c"]
    edges = q(client, "MATCH ()-[r]->() RETURN count(r) AS c")[0]["c"]
    print(f"  Total nodes: {nodes:,}  (expected 4,462)", flush=True)
    print(f"  Total edges: {edges:,}  (expected 8,363)", flush=True)

    print("\n--- REFERENCE NUMBERS (must match published demo) ---", flush=True)
    top = q(client, """
        MATCH (j:Judge)-[:DECIDED]->(c:Case)
        RETURN j.name AS judge, count(DISTINCT c) AS cases ORDER BY cases DESC LIMIT 1
    """)[0]
    print(f"  Top judge: {top['judge']} = {top['cases']}  (expected Dipak Misra = 104)", flush=True)

    ipc = q(client, """
        MATCH (c:Case)-[r:CITES]->(a:Act)
        WHERE a.name = "Indian Penal Code" AND r.section = "302"
        RETURN count(DISTINCT c) AS n
    """)[0]["n"]
    print(f"  IPC §302 cited in {ipc} judgments  (expected 57)", flush=True)

    art32 = q(client, """
        MATCH (c:Case)-[r:CITES]->(a:Act)
        WHERE a.name = "Constitution of India" AND r.section = "Article 32"
        RETURN count(DISTINCT c) AS n
    """)[0]["n"]
    print(f"  Constitution Article 32 cited in {art32} judgments  (expected 36)", flush=True)

    print("\n" + "=" * 60, flush=True)
    print("VERIFICATION COMPLETE", flush=True)


if __name__ == "__main__":
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "data"
    print(f"Loading data from {data_dir}...", flush=True)
    c = SamyamaClient.embedded()
    stats = load_legal_judgments(c, data_dir=data_dir)
    print(f"\nLoad complete: {stats}", flush=True)
    verify(c)
