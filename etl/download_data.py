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
import http.client
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO = "Shreyasrao/Indian-law-supreme-court-judgements-2016"
REVISION = "e928c72019d6"
API = f"https://huggingface.co/api/datasets/{REPO}/tree/{REVISION}/extracted_jsons?recursive=1"
RESOLVE = f"https://huggingface.co/datasets/{REPO}/resolve/{REVISION}"

RETRIES = 3
EXPECTED_FILES = 589   # judgment JSONs at this pinned REVISION; a mismatch flags truncation


def _get(url: str) -> bytes:
    """Fetch a URL, retrying with backoff on transient errors.

    A 4xx (client error, e.g. 404) is permanent, so it is raised immediately and not
    retried; only 5xx, connection and timeout errors are retried (429 is treated as
    transient too).
    """
    req = urllib.request.Request(url, headers={"User-Agent": "legal-judgments-graph-kg"})
    last = None
    for attempt in range(1, RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if 400 <= e.code < 500 and e.code != 429:
                raise RuntimeError(f"fetch {url} failed permanently: HTTP {e.code}") from e
            last = e
            if attempt < RETRIES:
                time.sleep(2 * attempt)
        except (urllib.error.URLError, TimeoutError, ConnectionError,
                http.client.HTTPException) as e:
            # Covers connection resets / drops (e.g. http.client.RemoteDisconnected) and
            # protocol errors, which HuggingFace can throw when rate-limiting rapid requests.
            last = e
            if attempt < RETRIES:
                time.sleep(2 * attempt)
    raise RuntimeError(f"failed to fetch {url} after {RETRIES} attempts: {last}")


def download_all(out: str = "data") -> None:
    out_dir = Path(out)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[download] listing {REPO} @ {REVISION} ...")
    tree = json.loads(_get(API))
    paths = [e["path"] for e in tree if e.get("path", "").endswith(".json")]
    print(f"[download] {len(paths)} judgment JSON files")
    if not paths:
        raise RuntimeError(
            "no judgment JSON files found — the dataset layout or revision may have "
            "changed. Check REPO/REVISION in etl/download_data.py."
        )
    if len(paths) != EXPECTED_FILES:
        print(
            f"[download]   WARN listed {len(paths)} files but expected {EXPECTED_FILES} "
            f"at revision {REVISION} — the tree API may be truncated/paginated, or the "
            f"dataset changed. Counts below may not match the documented totals."
        )

    records = []
    for i, p in enumerate(paths, 1):
        try:
            records.append(json.loads(_get(f"{RESOLVE}/{p}")))
        except (RuntimeError, json.JSONDecodeError) as e:
            print(f"[download]   WARN skipping {p}: {e}")
        time.sleep(0.05)   # gentle throttle — avoid HuggingFace dropping rapid back-to-back requests
        if i % 50 == 0 or i == len(paths):
            print(f"[download]   {i}/{len(paths)}")

    if not records:
        raise RuntimeError("no records were downloaded — aborting without writing CSVs.")

    _write_csvs(records, out_dir)
    print(f"[download] wrote CSVs into {out_dir}/")


def _write_csvs(records: list[dict], out: Path) -> None:
    """Flatten the judgment JSON into node + edge CSVs (dedup by exact string)."""
    judges, parties, acts = set(), set(), set()
    topics: dict[str, str] = {}
    cases, summaries = [], []
    e_dec, e_par, e_cit, e_abo = [], [], [], []

    skipped = 0
    for r in records:
        cid = r.get("filename") or r.get("doc_id")
        if not cid:                       # can't wire edges without a stable case id
            skipped += 1
            continue
        ent = r.get("entities", {})
        md = r.get("metadata", {})
        ct = ent.get("case_title")
        title = ct.get("title") if isinstance(ct, dict) else ct
        cases.append([cid, title or "", md.get("year") or "", md.get("month") or ""])
        sm = ent.get("summary")
        summary = sm.get("summary") if isinstance(sm, dict) else sm
        if summary:
            summaries.append([cid, summary])
        # dedup edges *within a case* so the same judge/party/topic/section isn't
        # wired to the same case twice.
        seen_dec, seen_par, seen_cit, seen_abo = set(), set(), set(), set()
        for j in ent.get("judges", []):
            n = (j.get("name") or "").strip()
            if n and n not in seen_dec:
                seen_dec.add(n)
                judges.add(n)
                e_dec.append([n, cid])
        for p in ent.get("parties", []):
            n = (p.get("name") or "").strip()
            role = p.get("role", "")
            if n and (n, role) not in seen_par:
                seen_par.add((n, role))
                parties.add(n)
                e_par.append([n, cid, role])
        for s in ent.get("sections", []):
            a = (s.get("act") or "").strip()
            sec = str(s.get("section") or "").strip()
            if a:
                acts.add(a)
                if (a, sec) not in seen_cit:
                    seen_cit.add((a, sec))
                    e_cit.append([cid, a, sec])
        for t in ent.get("topics", []):
            tx = (t.get("text") or "").strip()
            if tx:
                topics.setdefault(tx, (t.get("category") or "").strip())
                if tx not in seen_abo:
                    seen_abo.add(tx)
                    e_abo.append([cid, tx])

    def _safe(cell):
        # Neutralize CSV formula injection: a leading =,+,-,@ (or tab/CR) can execute
        # in spreadsheet apps. Prefix such *text* cells with a single quote — but leave
        # legitimate numbers (e.g. "-5", "+3") untouched.
        if isinstance(cell, str) and cell[:1] in ("=", "+", "-", "@", "\t", "\r"):
            try:
                float(cell)
            except ValueError:
                return "'" + cell
        return cell

    def w(name, header, rows):
        with (out / name).open("w", newline="", encoding="utf-8") as f:
            wr = csv.writer(f)
            wr.writerow(header)
            wr.writerows([[_safe(c) for c in row] for row in rows])

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
    if skipped:
        print(f"[download] skipped {skipped} record(s) with no case id")


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Download + flatten the legal-judgments dataset")
    ap.add_argument("--out", default="data", help="Output directory (default: data)")
    args = ap.parse_args(argv)
    download_all(args.out)


if __name__ == "__main__":
    main()
