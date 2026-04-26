"""SQLite connection management + migration runner."""
import os
import sqlite3
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def open_db(path: str) -> sqlite3.Connection:
    """Open a SQLite connection with project pragmas applied."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def _ensure_schema_version_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_version "
        "(version INTEGER PRIMARY KEY, applied_at REAL NOT NULL)"
    )


def run_migrations(conn: sqlite3.Connection) -> None:
    """Apply numbered .sql files in MIGRATIONS_DIR if not already applied."""
    import time
    _ensure_schema_version_table(conn)
    applied = {r[0] for r in conn.execute(
        "SELECT version FROM schema_version"
    ).fetchall()}

    for sql_file in sorted(MIGRATIONS_DIR.glob("*.sql")):
        version = int(sql_file.stem.split("_")[0])
        if version in applied:
            continue
        sql = sql_file.read_text()
        conn.executescript(sql)
        conn.execute(
            "INSERT INTO schema_version (version, applied_at) VALUES (?, ?)",
            (version, time.time()),
        )
