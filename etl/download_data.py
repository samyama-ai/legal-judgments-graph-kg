"""Download the Indian Supreme Court judgments dataset and build the load CSVs.

Fetches the 589 structured JSON files from the public HuggingFace dataset
(CC-BY-4.0), then flattens them into the 9 node/edge CSVs that `etl.loader`
consumes, plus `summaries.csv` for the optional semantic-search vectors.

    python -m etl.download_data                 # into ./data
    python -m etl.download_data --out mydata

Dataset: Shreyasrao/Indian-law-supreme-court-judgements-2016 (rev e928c72019d6)
Source:  Indian Supreme Court Judgments on AWS Open Data (Dattam Labs), CC-BY-4.0
"""
from __future__ import annotations

import argparse
import csv
import json
import urllib.request
from pathlib import Path

REPO = "Shreyasrao/Indian-law-supreme-court-judgements-2016"
REVISION = "e928c72019d6"
API = f"https://huggingface.co/api/datasets/{REPO}/tree/{REVISION}/extracted_jsons?recursive=1"
RESOLVE = f"https://huggingface.co/datasets/{REPO}/resolve/{REVISION}"


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "legal-judgments-graph-kg"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def download_all(out: str = "data") -> None:
    out_dir = Path(out)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[download] listing {REPO} @ {REVISION} ...")
    tree = json.loads(_get(API))
    paths = [e["path"] for e in tree if e.get("path", "").endswith(".json")]
    print(f"[download] {len(paths)} judgment JSON files")

    records = []
    for i, p in enumerate(paths, 1):
        records.append(json.loads(_get(f"{RESOLVE}/{p}")))
        if i % 50 == 0 or i == len(paths):
            print(f"[download]   {i}/{len(paths)}")

    _write_csvs(records, out_dir)
    print(f"[download] wrote CSVs into {out_dir}/")


def _write_csvs(records: list[dict], out: Path) -> None:
    """Flatten the judgment JSON into node + edge CSVs (dedup by exact string)."""
    judges, parties, acts = set(), set(), set()
    topics: dict[str, str] = {}
    cases, summaries = [], []
    e_dec, e_par, e_cit, e_abo = [], [], [], []

    for r in records:
        cid = r.get("filename") or r.get("doc_id")
        ent = r.get("entities", {})
        md = r.get("metadata", {})
        ct = ent.get("case_title")
        title = ct.get("title") if isinstance(ct, dict) else ct
        cases.append([cid, title or "", md.get("year") or "", md.get("month") or ""])
        sm = ent.get("summary")
        summary = sm.get("summary") if isinstance(sm, dict) else sm
        if summary:
            summaries.append([cid, summary])
        for j in ent.get("judges", []):
            n = (j.get("name") or "").strip()
            if n:
                judges.add(n)
                e_dec.append([n, cid])
        for p in ent.get("parties", []):
            n = (p.get("name") or "").strip()
            if n:
                parties.add(n)
                e_par.append([n, cid, p.get("role", "")])
        seen = set()
        for s in ent.get("sections", []):
            a = (s.get("act") or "").strip()
            sec = str(s.get("section") or "").strip()
            if a:
                acts.add(a)
                if (a, sec) not in seen:
                    seen.add((a, sec))
                    e_cit.append([cid, a, sec])
        for t in ent.get("topics", []):
            tx = (t.get("text") or "").strip()
            if tx:
                topics.setdefault(tx, (t.get("category") or "").strip())
                e_abo.append([cid, tx])

    def w(name, header, rows):
        with (out / name).open("w", newline="", encoding="utf-8") as f:
            wr = csv.writer(f)
            wr.writerow(header)
            wr.writerows(rows)

    w("cases.csv", ["id", "title", "year", "month"], cases)
    w("judges.csv", ["name"], [[x] for x in sorted(judges)])
    w("parties.csv", ["name"], [[x] for x in sorted(parties)])
    w("acts.csv", ["name"], [[x] for x in sorted(acts)])
    w("topics.csv", ["text", "category"], [[t, topics[t]] for t in sorted(topics)])
    w("edge_decided.csv", ["judge_name", "case_id"], e_dec)
    w("edge_party_in.csv", ["party_name", "case_id", "role"], e_par)
    w("edge_cites.csv", ["case_id", "act", "section"], e_cit)
    w("edge_about.csv", ["case_id", "topic_text"], e_abo)
    w("summaries.csv", ["case_id", "summary"], summaries)
    print(f"[download] cases={len(cases)} judges={len(judges)} parties={len(parties)} "
          f"acts={len(acts)} topics={len(topics)} summaries={len(summaries)}")


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Download + flatten the legal-judgments dataset")
    ap.add_argument("--out", default="data", help="Output directory (default: data)")
    args = ap.parse_args(argv)
    download_all(args.out)


if __name__ == "__main__":
    main()
