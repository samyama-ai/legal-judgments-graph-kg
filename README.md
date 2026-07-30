# Legal Judgments Knowledge Graph

**4,462 nodes. 8,363 edges. 589 Indian Supreme Court judgments (2016) — cases, judges, parties, cited acts (with sections) and topics.**

> Part of the **Samyama** ecosystem — loaded into and queried via the graph engine at [samyama-ai/samyama-graph](https://github.com/samyama-ai/samyama-graph).
> This repo holds the loader and source-data specifics for the KG.

<a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache_2.0-blue" alt="License"></a>

---

We loaded 589 Supreme Court of India judgments (their judges, parties, cited legal sections and topics) into one graph, then asked:

> *"Which legal sections are cited across the most judgments?"*

```cypher
MATCH (c:Case)-[r:CITES]->(a:Act)
RETURN a.name AS act, r.section AS section, count(DISTINCT c) AS cases
ORDER BY cases DESC LIMIT 5
```

| Act | Section | Cases |
|-----|---------|-----------|
| **Indian Penal Code** | **302** (murder) | **57** |
| Constitution of India | Article 32 | 36 |
| Indian Penal Code | 34 | 35 |
| Constitution of India | Article 14 | 31 |
| Constitution of India | Article 136 | 24 |

**A flat table gives you a leaderboard. A graph gives you connections** — which judges sit together, which laws are cited side by side, which statutes span the widest range of subjects. Powered by [Samyama Graph](https://github.com/samyama-ai/samyama-graph).

---

## Documentation

New here? Start with the guides:

| Guide | What it covers |
|-------|----------------|
| **[GETTING_STARTED.md](GETTING_STARTED.md)** | prerequisites (Python ≥ 3.10) · install · run the engine (Docker) · load the graph · first query |
| **[docs/QUERYING.md](docs/QUERYING.md)** | ask questions via **MCP (Claude)**, the **HTTP API**, or the **Samyama CLI** |
| [docs/schema.md](docs/schema.md) | node & edge model |
| [docs/100-queries.md](docs/100-queries.md) | 100 example Cypher queries |

---

## Schema

**5 node labels** — Topic (2,291), Party (1,102), Case (589), Act (446), Judge (34)

**4 edge types** — DECIDED, PARTY_IN, CITES, ABOUT

| Node label | Key properties |
|------------|----------------|
| Case | id, title, year, month |
| Judge | name |
| Party | name |
| Act | name |
| Topic | text, category |

| Relationship | Pattern | Count |
|---|---|---|
| `ABOUT` | Case → Topic | 3,041 |
| `CITES` | Case → Act (property: `section`) | 2,749 |
| `PARTY_IN` | Party → Case (property: `role`) | 1,309 |
| `DECIDED` | Judge → Case | 1,264 |

The cited **`section` lives on the `CITES` edge**, so section-level questions ("how many judgments cite IPC §302?") are answerable directly. See [`docs/schema.md`](docs/schema.md).

**Data source** — [`Shreyasrao/Indian-law-supreme-court-judgements-2016`](https://huggingface.co/datasets/Shreyasrao/Indian-law-supreme-court-judgements-2016) (revision `e928c72019d6`), originally from the Indian Supreme Court Judgments registry on AWS Open Data (Dattam Labs). **License: CC-BY-4.0.**

## Quick Start

**Full walkthrough → [GETTING_STARTED.md](GETTING_STARTED.md)** (prerequisites, Docker, loading, querying).

Fastest path — build the graph locally (**Python ≥ 3.10**):

```bash
python -m venv .venv && source .venv/bin/activate     # Python >= 3.10
pip install -r requirements.txt
python -m etl.download_data           # 589 judgments → 9 CSVs in ./data
python -m etl.loader --data-dir data  # build + load: 4,462 nodes / 8,363 edges (embedded, no engine)
```

To query it from **Claude / HTTP / CLI**, serve it on a running engine — see
[GETTING_STARTED.md](GETTING_STARTED.md) §4 and [docs/QUERYING.md](docs/QUERYING.md).

## Example Queries

```cypher
// Most productive judges
MATCH (j:Judge)-[:DECIDED]->(c:Case)
RETURN j.name AS judge, count(DISTINCT c) AS cases
ORDER BY cases DESC LIMIT 5
// Dipak Misra (104), T. S. Thakur (81), A. K. Sikri (74), Rohinton F. Nariman (74), Kurian Joseph (68)

// Judges who most often sit together
MATCH (j1:Judge)-[:DECIDED]->(c:Case)<-[:DECIDED]-(j2:Judge)
WHERE j1.name < j2.name
RETURN j1.name, j2.name, count(DISTINCT c) AS cases_together
ORDER BY cases_together DESC LIMIT 5
// Kurian Joseph & Rohinton F. Nariman lead with 55

// Laws spanning the widest range of topics (two-hop)
MATCH (a:Act)<-[:CITES]-(c:Case)-[:ABOUT]->(t:Topic)
RETURN a.name, count(DISTINCT t.category) AS topic_breadth, count(DISTINCT c) AS cases
ORDER BY topic_breadth DESC LIMIT 5
// Constitution of India — all 11 topic categories
```

See the full **[100-query showcase](docs/100-queries.md)** — from single-table aggregations to network intelligence that SQL cannot express.

## MCP Server

```bash
python -m mcp_server.server --data-dir data              # embedded
python -m mcp_server.server --url http://localhost:8080  # against a running Samyama server
python -m mcp_server.server --data-dir data --list-tools # see all auto-generated + custom tools
```

Custom tools include `top_judges`, `most_cited_sections`, `co_sitting_judges`, `laws_cited_together`, `laws_by_topic_breadth`, `docket_by_category`, `cases_by_judge`, `cases_citing_section`, `parties_in_case`, `judge_topic_focus` (see [`mcp_server/config.yaml`](mcp_server/config.yaml)).

## Benchmark

Samyama reproduces a public reference demo (Postgres + Apache AGE + pgvector) in a **single engine**, and on the same graph runs the analytical queries **8–36× faster** than Apache AGE (aggregation-heavy queries; 1.5× on the 2-hop join). Full head-to-head and method: [engine-repo case study](https://github.com/samyama-ai/samyama-graph/tree/main/case_studies/legal-judgments).

## Structure
```
etl/          # HuggingFace downloader + graph loader
mcp_server/   # MCP server exposing the KG (custom + auto-generated tools)
scripts/      # run_queries / verify_queries against a loaded graph
docs/         # schema + design notes
tests/        # pytest
pyproject.toml
```

## Links

| | |
|---|---|
| Samyama Graph | [github.com/samyama-ai/samyama-graph](https://github.com/samyama-ai/samyama-graph) |
| Case study (engine repo) | [case_studies/legal-judgments](https://github.com/samyama-ai/samyama-graph/tree/main/case_studies/legal-judgments) |
| Dataset | [huggingface.co/datasets/Shreyasrao/…-2016](https://huggingface.co/datasets/Shreyasrao/Indian-law-supreme-court-judgements-2016) |
| Contact | [samyama.dev/contact](https://samyama.dev/contact) |

## License

Apache 2.0. Source data is CC-BY-4.0 (Indian Supreme Court Judgments via AWS Open Data / Dattam Labs).
