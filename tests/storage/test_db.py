import os
import sqlite3
import tempfile
import pytest
from src.storage.db import open_db, run_migrations, MIGRATIONS_DIR


def test_open_db_applies_pragmas(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = open_db(db_path)
    assert conn.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"
    assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    assert conn.execute("PRAGMA synchronous").fetchone()[0] == 1  # NORMAL=1
    conn.close()


def test_run_migrations_creates_tables_and_records_version(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = open_db(db_path)
    run_migrations(conn)

    tables = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()}
    assert {"conversations", "runs", "events", "schema_version"} <= tables

    versions = [r[0] for r in conn.execute(
        "SELECT version FROM schema_version ORDER BY version"
    ).fetchall()]
    assert 1 in versions
    conn.close()


def test_run_migrations_is_idempotent(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = open_db(db_path)
    run_migrations(conn)
    run_migrations(conn)  # second call must not raise
    count = conn.execute("SELECT COUNT(*) FROM schema_version").fetchone()[0]
    assert count == 1
    conn.close()
