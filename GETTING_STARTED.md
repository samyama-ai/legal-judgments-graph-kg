# Getting Started — Legal Judgments KG

From `git clone` to your first answer. The **quick path runs fully embedded** (no server, no Docker).

---

## 1. Prerequisites

- **Python ≥ 3.10** — required by the `samyama` SDK. (macOS ships 3.9, which **will not install** this
  package — use `python3.10`+.)
- **git**
- **Docker** — *optional*, only for serving the graph to MCP / HTTP / CLI clients (see §4). The quick
  build below needs no engine.

## 2. Install

```bash
git clone https://git.samyama.ai/Samyama.ai/legal-judgments-graph-kg.git
cd legal-judgments-graph-kg
python3 -m venv .venv && source .venv/bin/activate     # Python >= 3.10
pip install -r requirements.txt                         # runtime deps
# (for tests/tooling instead:  pip install -e ".[dev]")
```

## 3. Build the graph — quick path (embedded, no engine)

```bash
python -m etl.download_data           # fetch 589 Supreme Court judgments (2016) → 9 CSVs in ./data
python -m etl.loader --data-dir data  # build + load: 4,462 nodes / 8,363 edges  (~9s, in-process)
```

That's enough to validate the pipeline end-to-end. To *query* the graph from Claude / HTTP / CLI,
serve it into a running engine — next.

## 4. Serve the graph (for MCP / HTTP / CLI queries)

Start the engine with Docker, then load into the `legal-judgments` tenant:

```bash
docker run --rm -p 8080:8080 -p 6379:6379 public.ecr.aws/f9f6l5u4/samyama-graph:1.1.0

python -m etl.download_data
python -m etl.loader --data-dir data --url http://localhost:8080   # load into the running engine
```

*(Once the prebuilt `.sgsnap` snapshot is published, you'll be able to import it in seconds instead —
that path is "coming soon" in the README.)*

## 5. Ask your first question

Fastest is **Claude over MCP** — full details in **[docs/QUERYING.md](docs/QUERYING.md)**. Quick check
over HTTP:

```bash
curl -s -X POST http://localhost:8080/api/query -H 'Content-Type: application/json' -d '{
  "graph": "legal-judgments",
  "query": "MATCH (j:Judge)-[:DECIDED]->(c:Case) RETURN j.name AS judge, count(DISTINCT c) AS cases ORDER BY cases DESC LIMIT 3"
}'
# → Dipak Misra (104), T. S. Thakur (81), Rohinton F. Nariman (74)
```

## 6. The ETL pipeline

Everything that builds the graph lives in **`etl/`**:

| File | Does |
|------|------|
| `etl/download_data.py` | fetch the 589 judgments from HuggingFace → 9 CSVs in `./data` |
| `etl/loader.py` | build the graph (nodes + edges); `--url` to load a running engine, `--embed` for vectors |

Run `python -m etl.loader --help` for all options.

## Next

- **[docs/QUERYING.md](docs/QUERYING.md)** — ask questions via MCP (Claude), HTTP API, or the Samyama CLI
- **[docs/schema.md](docs/schema.md)** — nodes, edges, properties
- **[docs/100-queries.md](docs/100-queries.md)** — 100 example queries
