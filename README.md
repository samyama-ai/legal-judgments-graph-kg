# Legal Judgments Knowledge Graph

**{{N}} nodes. {{M}} edges. Judgments, courts, judges, statutes, parties, and citations from {{K}} open legal sources.**

![Legal judgments demo](demo/legal-judgments.gif)

> Part of the **Samyama** ecosystem — loaded into and queried via the graph engine at [samyama-ai/samyama-graph](https://github.com/samyama-ai/samyama-graph).
> This repo holds the loader and source-data specifics for the KG.

<a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache_2.0-blue" alt="License"></a>

---

We loaded {{SOURCES}} into one graph, then asked:

> *"Which statute is cited across the most judgments?"*

```cypher
MATCH (j:Judgment)-[:INVOKES_STATUTE]->(s:Statute)
RETURN s.title, count(j) AS judgments
ORDER BY judgments DESC LIMIT 5
```

**One query across every court and statute.** Powered by [Samyama Graph](https://github.com/samyama-ai/samyama-graph).

---

## Demo

A narrated walkthrough on a fast, real subset: load -> most-cited precedents -> statutes invoked most often -> judges with the most reversed decisions.

```bash
python -m demo.demo                                                    # run live
asciinema rec --overwrite --cols 92 --rows 32 --idle-time-limit 2.0 \
  -c "bash -c 'python -m demo.demo'" demo/legal-judgments.cast         # re-record
agg demo/legal-judgments.cast demo/legal-judgments.gif                 # convert to gif
```

---

## Schema

**Node labels** -- Judgment, Court, Judge, Statute, Party, Citation
**Edge types** -- DECIDED_BY, HEARD_IN, INVOKES_STATUTE, INVOLVES_PARTY, CITES
**Data sources** -- {{SOURCES}}

See [`schema/legal_judgments_kg.cypher`](schema/legal_judgments_kg.cypher) for the full schema.

## Quick Start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .

python -m etl.download_data          # fetch source data into data/
python -m etl.loader                 # build + load the graph
python -m mcp_server.server          # expose the KG over MCP
pytest                               # run tests
```

## Structure
```
etl/          # downloaders + graph loader
schema/       # cypher schema / ontology
mcp_server/   # MCP server exposing the KG
demo/         # narrated demo (cast + gif)
benchmarks/   # benchmark queries
docs/         # design + source notes
tests/        # pytest
pyproject.toml
```

---
_Created from the `legal-judgments-graph-kg` template. Replace the `{{...}}` placeholders and the schema/loaders for your KG._
