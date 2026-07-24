"""Smoke tests — replace with real schema/loader assertions."""
from etl.helpers import norm_id


def test_norm_id():
    assert norm_id("court", "Supreme Court") == "court:supreme_court"
