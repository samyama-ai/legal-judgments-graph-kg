"""Verify graph statistics and the reference demo's published numbers after a full load.

Compares actual results against the EXPECTED constants below and exits non-zero on any
mismatch, so it's usable in CI. Expected values live in one place (EXPECTED).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
from samyama import SamyamaClient
from etl.loader import load_legal_judgments

GRAPH = "legal-judgments"

# Single source of truth for the numbers this KG must reproduce.
EXPECTED = {
    "nodes": 4462,
    "edges": 8363,
    "top_judge": ("Dipak Misra", 104),
    "ipc_302": 57,               # judgments citing Indian Penal Code section 302
    "constitution_art32": 36,    # judgments citing Constitution of India Article 32
}


def q(client, cypher):
    r = client.query_readonly(cypher, GRAPH)
    return [dict(zip(r.columns, row)) for row in r.records]


def _scalar(client, cypher, default=0):
    rows = q(client, cypher)
    if not rows:
        return default
    return list(rows[0].values())[0]


def verify(client) -> int:
    failures = []

    def check(name, actual, expected):
        ok = actual == expected
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {actual}  (expected {expected})", flush=True)
        if not ok:
            failures.append(name)

    print("=" * 60, flush=True)
    print("VERIFYING LEGAL-JUDGMENTS-KG NUMBERS", flush=True)
    print("=" * 60, flush=True)

    nodes = _scalar(client, "MATCH (n) RETURN count(n) AS c")
    edges = _scalar(client, "MATCH ()-[r]->() RETURN count(r) AS c")
    check("total nodes", nodes, EXPECTED["nodes"])
    check("total edges", edges, EXPECTED["edges"])

    top = q(client, "MATCH (j:Judge)-[:DECIDED]->(c:Case) "
                    "RETURN j.name AS judge, count(DISTINCT c) AS cases ORDER BY cases DESC LIMIT 1")
    top = top[0] if top else {"judge": None, "cases": 0}
    check("top judge", (top["judge"], top["cases"]), EXPECTED["top_judge"])

    ipc = _scalar(client, 'MATCH (c:Case)-[r:CITES]->(a:Act) '
                          'WHERE a.name = "Indian Penal Code" AND r.section = "302" '
                          'RETURN count(DISTINCT c) AS c')
    check("IPC §302 judgments", ipc, EXPECTED["ipc_302"])

    art32 = _scalar(client, 'MATCH (c:Case)-[r:CITES]->(a:Act) '
                            'WHERE a.name = "Constitution of India" AND r.section = "Article 32" '
                            'RETURN count(DISTINCT c) AS c')
    check("Constitution Article 32 judgments", art32, EXPECTED["constitution_art32"])

    print("=" * 60, flush=True)
    if failures:
        print(f"FAILED: {len(failures)} mismatch(es): {', '.join(failures)}", flush=True)
        return 1
    print("VERIFICATION PASSED — all numbers match.", flush=True)
    return 0


if __name__ == "__main__":
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "data"
    print(f"Loading data from {data_dir}...", flush=True)
    c = SamyamaClient.embedded()
    load_legal_judgments(c, data_dir=data_dir)
    sys.exit(verify(c))
