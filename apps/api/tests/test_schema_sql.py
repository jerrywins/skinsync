"""Applies the migration to a fresh database and runs the SQL integrity tests (NFR-09, FR-19, FR-20, SC-05)."""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

HERE = Path(__file__).parent
PG = dict(host=os.environ.get("PGHOST", "localhost"), user=os.environ.get("PGUSER", "postgres"))
DB = "skinsync_schema_test"


def psql(*args, db="postgres"):
    return subprocess.run(["psql", "-h", PG["host"], "-U", PG["user"], "-d", db, "-X", "-v", "ON_ERROR_STOP=1", *args],
                          capture_output=True, text=True)


pytestmark = pytest.mark.skipif(shutil.which("psql") is None or psql("-c", "select 1").returncode != 0,
                                reason="PostgreSQL not reachable")


def test_migration_applies_and_constraints_hold():
    psql("-c", f"DROP DATABASE IF EXISTS {DB}")
    assert psql("-c", f"CREATE DATABASE {DB}").returncode == 0
    try:
        for f in sorted((HERE.parent / "migrations").glob("*.sql")):
            mig = psql("-q", "--single-transaction", "-f", str(f), db=DB)
            assert mig.returncode == 0, mig.stderr
        res = psql("-q", "-f", str(HERE / "sql" / "schema_constraints.sql"), db=DB)
        assert res.returncode == 0, res.stderr
        assert "ALL SCHEMA TESTS PASSED" in res.stdout
    finally:
        psql("-c", f"DROP DATABASE IF EXISTS {DB}")
