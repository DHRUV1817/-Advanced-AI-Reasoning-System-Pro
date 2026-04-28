"""Data access functions for conversations and runs.

Events DAO lives separately in src/core/event_bus.py because writes are
driven by the bus.
"""
import json
import time
import uuid
import sqlite3
from typing import Optional


def create_conversation(conn: sqlite3.Connection, title: Optional[str] = None,
                        metadata: Optional[dict] = None) -> str:
    cid = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO conversations (id, created_at, title, metadata) "
        "VALUES (?, ?, ?, ?)",
        (cid, time.time(), title, json.dumps(metadata) if metadata else None),
    )
    return cid


def list_conversations(conn: sqlite3.Connection, limit: int = 100,
                       offset: int = 0) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM conversations ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (limit, offset),
    ).fetchall()


def create_run(conn: sqlite3.Connection, *, conversation_id: str, query: str,
               strategy: str, reasoning_model: str, knobs: dict,
               evaluator_model: Optional[str] = None) -> str:
    rid = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO runs (id, conversation_id, created_at, status, strategy, "
        "reasoning_model, evaluator_model, query, knobs, tokens_used) "
        "VALUES (?, ?, ?, 'running', ?, ?, ?, ?, ?, 0)",
        (rid, conversation_id, time.time(), strategy, reasoning_model,
         evaluator_model, query, json.dumps(knobs)),
    )
    return rid


def get_run(conn: sqlite3.Connection, run_id: str) -> Optional[sqlite3.Row]:
    return conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()


def list_runs(conn: sqlite3.Connection, *, conversation_id: Optional[str] = None,
              status: Optional[str] = None, strategy: Optional[str] = None,
              limit: int = 100, offset: int = 0) -> list[sqlite3.Row]:
    where, params = [], []
    if conversation_id:
        where.append("conversation_id = ?"); params.append(conversation_id)
    if status:
        where.append("status = ?"); params.append(status)
    if strategy:
        where.append("strategy = ?"); params.append(strategy)
    sql = "SELECT * FROM runs"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params += [limit, offset]
    return conn.execute(sql, params).fetchall()


def complete_run(conn: sqlite3.Connection, run_id: str, *, final_answer: str,
                 confidence: float, tokens_used: int, elapsed_s: float) -> None:
    conn.execute(
        "UPDATE runs SET status='completed', completed_at=?, final_answer=?, "
        "confidence=?, tokens_used=?, elapsed_s=? WHERE id=?",
        (time.time(), final_answer, confidence, tokens_used, elapsed_s, run_id),
    )


def fail_run(conn: sqlite3.Connection, run_id: str, *, error: str) -> None:
    conn.execute(
        "UPDATE runs SET status='failed', completed_at=?, error=? WHERE id=?",
        (time.time(), error, run_id),
    )


def cancel_run(conn: sqlite3.Connection, run_id: str) -> None:
    conn.execute(
        "UPDATE runs SET status='aborted', completed_at=? WHERE id=?",
        (time.time(), run_id),
    )


def update_tokens(conn: sqlite3.Connection, run_id: str, delta: int) -> None:
    conn.execute(
        "UPDATE runs SET tokens_used = tokens_used + ? WHERE id = ?",
        (delta, run_id),
    )
