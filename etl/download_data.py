"""Download source legal-judgment data into ./data.

Replace the stubs below with real source fetchers (court APIs, open judgment
datasets, statute registries). Keep each source in its own function.
"""
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def download_all() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    # TODO: implement per-source downloads, e.g.:
    # download_judgments()
    # download_statutes()
    print(f"[download] wrote sources into {DATA_DIR}")


if __name__ == "__main__":
    download_all()
