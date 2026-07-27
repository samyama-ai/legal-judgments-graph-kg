"""
Legal Judgments Knowledge Graph ETL Loader
===========================================
Loads 589 Indian Supreme Court judgments (2016) into a Samyama property graph.
Creates Case, Judge, Party, Act and Topic nodes plus DECIDED, PARTY_IN,
CITES (with the cited section on the edge) and ABOUT edges.

Schema: 5 node labels, 4 edge types.
  Case{id,title,year,month}
  Judge{name}
  Party{name}
  Act{name}
  Topic{text,category}

  (:Judge)-[:DECIDED]->(:Case)
  (:Party)-[:PARTY_IN]->(:Case)          {role}
  (:Case)-[:CITES]->(:Act)               {section}   -- section kept on the edge
  (:Case)-[:ABOUT]->(:Topic)

Reads the 9 CSV files produced by `python -m etl.download_data` from --data-dir:
  cases.csv  judges.csv  parties.csv  acts.csv  topics.csv
  edge_decided.csv  edge_party_in.csv  edge_cites.csv  edge_about.csv

Optional (semantic search): with --embed, each Case's `summary` is embedded with
sentence-transformers and stored as a vector for k-NN search (mirrors the
reference demo's pgvector layer, but in the same engine).

Data source: https://huggingface.co/datasets/Shreyasrao/Indian-law-supreme-court-judgements-2016
License: CC-BY-4.0 (source data via AWS Open Data / Dattam Labs)

Usage:
    python -m etl.loader --data-dir data
    python -m etl.loader --data-dir data --limit 50        # fast subset
    python -m etl.loader --data-dir data --embed           # + semantic vectors
    python -m etl.loader --data-dir data --url http://localhost:8080
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

from samyama import SamyamaClient

from etl.helpers import GRAPH, batch_create_nodes, batch_create_edges, read_csv, _q


def _int(val):
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def load_legal_judgments(
    client: SamyamaClient,
    data_dir: str = "data",
    limit: int | None = None,
    embed: bool = False,
) -> dict:
    """Load the legal-judgments CSVs into Samyama. Returns a dict of counts."""
    d = Path(data_dir)
    counts = {"cases": 0, "judges": 0, "parties": 0, "acts": 0, "topics": 0,
              "DECIDED": 0, "PARTY_IN": 0, "CITES": 0, "ABOUT": 0}

    # --- indexes (best-effort; speeds up the edge MATCHes) ---
    indexes = [("Case", "id"), ("Judge", "name"), ("Party", "name"),
               ("Act", "name"), ("Topic", "text")]
    for label, prop in indexes:
        try:
            client.query(f"CREATE INDEX ON :{label}({prop})", GRAPH)
        except Exception as e:
            print(f"  [index] skipped :{label}({prop}) — {e}", flush=True)
    print(f"Created {len(indexes)} indexes", flush=True)

    t0 = time.time()

    # ---- NODES ----
    print("Phase 1/2: Loading nodes ...", flush=True)
    judges = read_csv(d / "judges.csv")
    batch_create_nodes(client, [("Judge", {"name": r["name"]}) for r in judges])
    counts["judges"] = len(judges)

    parties = read_csv(d / "parties.csv")
    batch_create_nodes(client, [("Party", {"name": r["name"]}) for r in parties])
    counts["parties"] = len(parties)

    acts = read_csv(d / "acts.csv")
    batch_create_nodes(client, [("Act", {"name": r["name"]}) for r in acts])
    counts["acts"] = len(acts)

    topics = read_csv(d / "topics.csv")
    batch_create_nodes(client, [("Topic", {"text": r["text"], "category": r.get("category", "")}) for r in topics])
    counts["topics"] = len(topics)

    cases = read_csv(d / "cases.csv")
    if limit is not None:          # honor --limit 0 (load 0 cases) instead of treating 0 as "all"
        cases = cases[:limit]
    keep = {r["id"] for r in cases}          # case ids we actually loaded
    batch_create_nodes(client, [
        ("Case", {"id": r["id"], "title": r.get("title", ""),
                  "year": _int(r.get("year")), "month": _int(r.get("month"))})
        for r in cases
    ])
    counts["cases"] = len(cases)

    # ---- EDGES ---- (only for cases we kept, so --limit stays consistent)
    print("Phase 2/2: Loading edges ...", flush=True)

    dec = [r for r in read_csv(d / "edge_decided.csv") if r["case_id"] in keep]
    batch_create_edges(client, [
        ("Judge", f"name: {_q(r['judge_name'])}", "DECIDED", "Case", f"id: {_q(r['case_id'])}", None)
        for r in dec
    ])
    counts["DECIDED"] = len(dec)

    par = [r for r in read_csv(d / "edge_party_in.csv") if r["case_id"] in keep]
    batch_create_edges(client, [
        ("Party", f"name: {_q(r['party_name'])}", "PARTY_IN", "Case", f"id: {_q(r['case_id'])}",
         {"role": r.get("role", "")} if r.get("role") else None)
        for r in par
    ])
    counts["PARTY_IN"] = len(par)

    cit = [r for r in read_csv(d / "edge_cites.csv") if r["case_id"] in keep]
    batch_create_edges(client, [
        ("Case", f"id: {_q(r['case_id'])}", "CITES", "Act", f"name: {_q(r['act'])}",
         {"section": r.get("section", "")})
        for r in cit
    ])
    counts["CITES"] = len(cit)

    abo = [r for r in read_csv(d / "edge_about.csv") if r["case_id"] in keep]
    batch_create_edges(client, [
        ("Case", f"id: {_q(r['case_id'])}", "ABOUT", "Topic", f"text: {_q(r['topic_text'])}", None)
        for r in abo
    ])
    counts["ABOUT"] = len(abo)

    # ---- OPTIONAL: semantic vectors on Case.summary ----
    if embed:
        _load_embeddings(client, d, cases)

    elapsed = time.time() - t0
    counts["nodes"] = counts["cases"] + counts["judges"] + counts["parties"] + counts["acts"] + counts["topics"]
    counts["edges"] = counts["DECIDED"] + counts["PARTY_IN"] + counts["CITES"] + counts["ABOUT"]

    print(f"\n{'='*60}", flush=True)
    print(f"Legal Judgments KG load complete in {elapsed:.1f}s", flush=True)
    print(f"{'='*60}", flush=True)
    for k, v in counts.items():
        print(f"  {k:<12s} {v}", flush=True)
    return counts


def _load_embeddings(client, data_dir: Path, cases: list[dict]) -> None:
    """Embed each Case's `summary` and store it as a vector for k-NN search.

    Requires `summaries.csv` (case_id,summary) from download_data.py and the
    `sentence-transformers` extra. Uses the same 1024-dim model family the
    reference pgvector setup used, so the two are comparable.
    """
    summaries = {r["case_id"]: r.get("summary", "") for r in read_csv(data_dir / "summaries.csv")}
    if not summaries:
        print("  [embed] no summaries.csv found — skipping vectors", flush=True)
        return
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("  [embed] sentence-transformers not installed — skipping vectors", flush=True)
        return

    model = SentenceTransformer("mixedbread-ai/mxbai-embed-large-v1")   # 1024-dim
    dim = model.get_sentence_embedding_dimension()

    # Create the HNSW index via the SDK (NOT Cypher — there is no CREATE VECTOR INDEX).
    client.create_vector_index("Case", "embedding", dim, "cosine")

    # add_vector needs the engine's INTERNAL node id, so map our Case.id -> id(n).
    r = client.query_readonly("MATCH (n:Case) RETURN id(n) AS nid, n.id AS cid", GRAPH)
    idmap = {row[1]: row[0] for row in r.records}

    n = 0
    for row in cases:
        text = summaries.get(row["id"], "").strip()
        nid = idmap.get(row["id"])
        if not text or nid is None:
            continue
        vec = model.encode(text, normalize_embeddings=True).tolist()
        client.add_vector("Case", "embedding", nid, vec)
        n += 1
    print(f"  [embed] stored {n} case-summary vectors ({dim}-dim, cosine)", flush=True)


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Load Indian Supreme Court judgments into Samyama")
    ap.add_argument("--data-dir", default="data", help="Directory with the 9 CSV files")
    ap.add_argument("--limit", type=int, default=None, help="Cap the number of cases (fast demo)")
    ap.add_argument("--embed", action="store_true", help="Also embed case summaries for semantic search")
    ap.add_argument("--url", default=None, help="Samyama server URL (omit for embedded)")
    args = ap.parse_args(argv)

    client = SamyamaClient.connect(args.url) if args.url else SamyamaClient.embedded()
    load_legal_judgments(client, data_dir=args.data_dir, limit=args.limit, embed=args.embed)


if __name__ == "__main__":
    main()
