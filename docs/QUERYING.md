# Querying the Legal Judgments KG

Three ways to ask the graph questions, once it's served on a running engine (see
[GETTING_STARTED.md](../GETTING_STARTED.md) §4). Tenant/graph name: **`legal-judgments`**.

All three below were run against a live engine and return the same result.

---

## 1. Claude, over MCP (natural language)

Let Claude pick the tool and query the graph for you — ask in plain English.

```bash
# register this KG's MCP server with Claude Code (once):
claude mcp add samyama-legal -- \
  samyama-mcp-serve --graph legal-judgments --url http://localhost:8080 \
  --config mcp_server/config.yaml

# start a new Claude Code session (MCP servers load at session start), then just ask:
#   "Which judge decided the most cases?"      → Dipak Misra — 104
#   "Which legal sections are cited the most?" → IPC §302 — 57
```

`--config mcp_server/config.yaml` adds the curated tools (`top_judges`, `most_cited_sections`,
`co_sitting_judges`, `laws_cited_together`, `laws_by_topic_breadth`). Without it, the SDK
auto-generates tools from the schema (`count_case`, `search_judge`, `cypher_query`, …).

## 2. HTTP API (`POST /api/query`)

```bash
curl -s -X POST http://localhost:8080/api/query -H 'Content-Type: application/json' -d '{
  "graph": "legal-judgments",
  "query": "MATCH (j:Judge)-[:DECIDED]->(c:Case) RETURN j.name AS judge, count(DISTINCT c) AS cases ORDER BY cases DESC LIMIT 3"
}'
```
```json
{"columns":["judge","cases"],
 "records":[["Dipak Misra",104],["T. S. Thakur",81],["Rohinton F. Nariman",74]]}
```

## 3. Samyama CLI (Redis wire protocol, `:6379`)

Samyama speaks the Redis protocol, so any Redis client works:

```bash
redis-cli -p 6379 GRAPH.QUERY legal-judgments \
  "MATCH (j:Judge)-[:DECIDED]->(c:Case) RETURN j.name, count(DISTINCT c) AS n ORDER BY n DESC LIMIT 3"
# 1) "Dipak Misra"  104
# 2) "T. S. Thakur"  81
# 3) "Rohinton F. Nariman"  74
```

---

## More queries

See **[100-queries.md](100-queries.md)** for 100 example Cypher queries (foundation → multi-hop graph
questions), and **[schema.md](schema.md)** for the node/edge model.
