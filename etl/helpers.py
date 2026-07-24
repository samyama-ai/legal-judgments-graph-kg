"""Shared ETL helpers (parsing, normalization, id minting)."""


def norm_id(prefix: str, value: str) -> str:
    """Stable node id from a source key."""
    return f"{prefix}:{value.strip().lower().replace(' ', '_')}"
