"""Tests for legal-judgments-kg MCP server — verifies auto-generated + custom tools.

Uses a tiny synthetic fixture with known values so the custom-tool results can be
asserted exactly. Runs only if `samyama` + `samyama_mcp` are installed.
"""
import asyncio
import json
import os
import sys
import tempfile

import pytest

pytest.importorskip("samyama")
pytest.importorskip("samyama_mcp")

from samyama import SamyamaClient
from samyama_mcp.config import ToolConfig
from samyama_mcp.server import SamyamaMCPServer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from etl.loader import load_legal_judgments

# --- synthetic fixture (known values for exact assertions) ---
# Dipak Misra decides c1 (with T.S.Thakur) and c2  -> top judge = 2 cases
# IPC §302 cited in c1 and c2 -> 2 ; Constitution Art 32 in c1 -> 1
CASES = "id,title,year,month\nc1,A v. B,2016,1\nc2,C v. D,2016,2\n"
JUDGES = "name\nDipak Misra\nT. S. Thakur\n"
PARTIES = "name\nState of X\n"
ACTS = "name\nIndian Penal Code\nConstitution of India\n"
TOPICS = "text,category\nMurder,criminal\nBail,procedural\n"
E_DECIDED = "judge_name,case_id\nDipak Misra,c1\nT. S. Thakur,c1\nDipak Misra,c2\n"
E_PARTY = "party_name,case_id,role\nState of X,c1,appellant\n"
E_CITES = ("case_id,act,section\n"
           "c1,Indian Penal Code,302\nc1,Constitution of India,Article 32\n"
           "c2,Indian Penal Code,302\n")
E_ABOUT = "case_id,topic_text\nc1,Murder\nc1,Bail\nc2,Murder\n"


def _write(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


@pytest.fixture(scope="module")
def server():
    client = SamyamaClient.embedded()
    with tempfile.TemporaryDirectory() as d:
        for name, content in {
            "cases.csv": CASES, "judges.csv": JUDGES, "parties.csv": PARTIES,
            "acts.csv": ACTS, "topics.csv": TOPICS, "edge_decided.csv": E_DECIDED,
            "edge_party_in.csv": E_PARTY, "edge_cites.csv": E_CITES, "edge_about.csv": E_ABOUT,
        }.items():
            _write(os.path.join(d, name), content)
        load_legal_judgments(client, data_dir=d)

    config_path = os.path.join(os.path.dirname(__file__), "..", "mcp_server", "config.yaml")
    config = ToolConfig.from_yaml(config_path)
    return SamyamaMCPServer(client, server_name="Legal Judgments KG Test", config=config)


def _call(server, tool_name, args=None):
    async def _run():
        r = await server.mcp.call_tool(tool_name, args or {})
        return json.loads(r.content[0].text)
    return asyncio.run(_run())


class TestToolRegistration:
    def test_generic_and_custom_tools_present(self, server):
        tools = server.list_tools()
        assert "cypher_query" in tools
        assert "schema_info" in tools
        for t in ["top_judges", "most_cited_sections", "co_sitting_judges",
                  "laws_cited_together", "laws_by_topic_breadth", "docket_by_category",
                  "cases_by_judge", "cases_citing_section", "parties_in_case", "judge_topic_focus"]:
            assert t in tools, f"missing custom tool: {t}"

    def test_has_node_and_edge_tools(self, server):
        tools = server.list_tools()
        assert "search_case" in tools
        assert "count_judge" in tools
        assert "find_decided_connections" in tools


class TestSchemaInfo:
    def test_labels_and_edges(self, server):
        schema = _call(server, "schema_info")
        labels = {nt["label"] for nt in schema["node_types"]}
        assert {"Case", "Judge", "Party", "Act", "Topic"} <= labels
        etypes = {et["type"] for et in schema["edge_types"]}
        assert {"DECIDED", "CITES", "ABOUT"} <= etypes


class TestCustomTools:
    def test_top_judges(self, server):
        rows = _call(server, "top_judges", {"limit": 5})
        assert rows[0]["judge"] == "Dipak Misra"
        assert rows[0]["cases"] == 2

    def test_most_cited_sections(self, server):
        rows = _call(server, "most_cited_sections", {"limit": 5})
        top = rows[0]
        assert top["act"] == "Indian Penal Code" and top["section"] == "302" and top["cases"] == 2

    def test_co_sitting_judges(self, server):
        rows = _call(server, "co_sitting_judges", {"limit": 5})
        assert rows[0]["cases_together"] == 1

    def test_laws_cited_together(self, server):
        rows = _call(server, "laws_cited_together", {"limit": 5})
        assert rows[0]["cited_together"] == 1

    def test_docket_by_category(self, server):
        rows = _call(server, "docket_by_category")
        cats = {r["category"]: r["mentions"] for r in rows}
        assert cats.get("criminal") == 2   # Murder in c1 and c2

    def test_cases_by_judge(self, server):
        rows = _call(server, "cases_by_judge", {"judge_name": "Dipak Misra"})
        assert len(rows) == 2

    def test_cases_citing_section(self, server):
        rows = _call(server, "cases_citing_section", {"act": "Indian Penal Code", "section": "302"})
        assert len(rows) == 2

    def test_judge_topic_focus(self, server):
        rows = _call(server, "judge_topic_focus", {"judge_name": "Dipak Misra"})
        cats = {r["category"]: r["cases"] for r in rows}
        assert cats.get("criminal") == 2


class TestSecurity:
    def test_cypher_query_rejects_write(self, server):
        result = _call(server, "cypher_query", {"cypher": "CREATE (n:Test)"})
        assert "error" in result

    def test_cypher_query_readonly_works(self, server):
        rows = _call(server, "cypher_query", {"cypher": "MATCH (n:Case) RETURN count(n) AS c"})
        assert rows[0]["c"] == 2
