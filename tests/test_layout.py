"""The package imports, and the curated data names a source for every row."""
import csv
import importlib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("name", ["dcopt", "dcopt.heat", "dcopt.grid", "dcopt.siting", "dcopt.common"])
def test_imports(name):
    assert importlib.import_module(name) is not None


def test_data_centers_have_sources_and_load_ranges():
    path = ROOT / "data" / "curated" / "ishikari_data_centers.csv"
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    assert rows, "no data centers listed"
    for r in rows:
        assert r["sources"].startswith("https://"), r["key"]
        assert 0 <= float(r["it_load_mw_low"]) <= float(r["it_load_mw_high"]), r["key"]
