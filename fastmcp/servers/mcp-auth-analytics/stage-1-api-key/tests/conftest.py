import importlib.util
import tempfile
from pathlib import Path

import pytest
from analytics_mcp import db

ROOT = Path(__file__).resolve().parents[1]


def _seed_module():
    spec = importlib.util.spec_from_file_location("seed", ROOT / "scripts" / "seed.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="session")
def seeded_path(tmp_path_factory):
    """One seeded DuckDB file for the session; tests that write copy it."""
    seed = _seed_module()
    folder = tmp_path_factory.mktemp("seed")
    path = folder / "analytics.duckdb"
    csvs = Path(tempfile.mkdtemp())
    seed.generate(csvs)
    con = db.duckdb.connect(str(path))
    seed.load(con, csvs)
    con.close()
    return path


@pytest.fixture
def warehouse(seeded_path, tmp_path, monkeypatch):
    copy = tmp_path / "analytics.duckdb"
    copy.write_bytes(seeded_path.read_bytes())
    monkeypatch.setattr(db, "LOCAL_PATH", copy)
    monkeypatch.setenv("ANALYTICS_DB", "local")
    return copy
