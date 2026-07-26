"""Smoke tests for the Legal Judgments KG.

Pure-Python helper tests always run. The end-to-end loader test runs only if the
`samyama` SDK is installed (embedded mode), mirroring football-kg's test_loader.
"""
import os
import tempfile

import pytest

from etl.helpers import prop_str, _escape


# --- pure helpers (no SDK needed) ---
def test_escape_strips_quotes_and_newlines():
    assert _escape('a"b\nc') == "ab c"   # quotes dropped, newline -> space
    assert _escape(None) == ""


def test_prop_str_types():
    s = prop_str({"name": "IPC", "year": 2016, "flag": True, "skip": None})
    assert 'name: "IPC"' in s
    assert "year: 2016" in s
    assert "flag: true" in s
    assert "skip" not in s          # None values are dropped


# --- end-to-end loader (needs the samyama SDK) ---
CASES = "id,title,year,month\nc1,A v. B,2016,1\nc2,C v. D,2016,2\n"
JUDGES = "name\nDipak Misra\nT. S. Thakur\n"
PARTIES = "name\nState of X\n"
ACTS = "name\nIndian Penal Code\n"
TOPICS = "text,category\nMurder,criminal\n"
E_DECIDED = "judge_name,case_id\nDipak Misra,c1\nT. S. Thakur,c1\nDipak Misra,c2\n"
E_PARTY = "party_name,case_id,role\nState of X,c1,appellant\n"
E_CITES = "case_id,act,section\nc1,Indian Penal Code,302\n"
E_ABOUT = "case_id,topic_text\nc1,Murder\n"


def test_load_legal_judgments_embedded():
    pytest.importorskip("samyama")
    from samyama import SamyamaClient
    from etl.loader import load_legal_judgments

    with tempfile.TemporaryDirectory() as d:
        files = {
            "cases.csv": CASES, "judges.csv": JUDGES, "parties.csv": PARTIES,
            "acts.csv": ACTS, "topics.csv": TOPICS, "edge_decided.csv": E_DECIDED,
            "edge_party_in.csv": E_PARTY, "edge_cites.csv": E_CITES, "edge_about.csv": E_ABOUT,
        }
        for name, content in files.items():
            with open(os.path.join(d, name), "w") as f:
                f.write(content)

        client = SamyamaClient.embedded()
        counts = load_legal_judgments(client, data_dir=d)

    assert counts["cases"] == 2
    assert counts["judges"] == 2
    assert counts["DECIDED"] == 3
    assert counts["CITES"] == 1
    assert counts["nodes"] == 2 + 2 + 1 + 1 + 1      # cases+judges+parties+acts+topics
