import json
import pytest
from src.storage.db import open_db, run_migrations
from src.storage.dao import (
    create_conversation, list_conversations,
    create_run, get_run, list_runs, complete_run, fail_run, update_tokens,
)


@pytest.fixture
def db(tmp_path):
    conn = open_db(str(tmp_path / "t.db"))
    run_migrations(conn)
    yield conn
    conn.close()


def test_create_and_list_conversation(db):
    cid = create_conversation(db, title="hello")
    assert isinstance(cid, str) and len(cid) > 0
    convs = list_conversations(db)
    assert any(c["id"] == cid and c["title"] == "hello" for c in convs)


def test_create_run_returns_row_with_running_status(db):
    cid = create_conversation(db)
    rid = create_run(db, conversation_id=cid, query="2+2?",
                     strategy="tot", reasoning_model="m1",
                     evaluator_model="e1", knobs={"branching_factor": 3})
    row = get_run(db, rid)
    assert row["status"] == "running"
    assert row["query"] == "2+2?"
    assert row["strategy"] == "tot"
    assert json.loads(row["knobs"]) == {"branching_factor": 3}
    assert row["tokens_used"] == 0
    assert row["final_answer"] is None


def test_complete_run_persists_result(db):
    cid = create_conversation(db)
    rid = create_run(db, conversation_id=cid, query="q",
                     strategy="sc", reasoning_model="m", knobs={})
    complete_run(db, rid, final_answer="42", confidence=0.8,
                 tokens_used=1234, elapsed_s=1.5)
    row = get_run(db, rid)
    assert row["status"] == "completed"
    assert row["final_answer"] == "42"
    assert row["confidence"] == 0.8
    assert row["tokens_used"] == 1234
    assert row["elapsed_s"] == 1.5
    assert row["completed_at"] is not None


def test_fail_run_persists_error(db):
    cid = create_conversation(db)
    rid = create_run(db, conversation_id=cid, query="q",
                     strategy="tot", reasoning_model="m", knobs={})
    fail_run(db, rid, error="boom")
    row = get_run(db, rid)
    assert row["status"] == "failed"
    assert row["error"] == "boom"


def test_update_tokens_accumulates(db):
    cid = create_conversation(db)
    rid = create_run(db, conversation_id=cid, query="q",
                     strategy="tot", reasoning_model="m", knobs={})
    update_tokens(db, rid, 100)
    update_tokens(db, rid, 50)
    assert get_run(db, rid)["tokens_used"] == 150


def test_list_runs_filters_and_orders(db):
    cid = create_conversation(db)
    r1 = create_run(db, conversation_id=cid, query="a", strategy="tot",
                    reasoning_model="m", knobs={})
    r2 = create_run(db, conversation_id=cid, query="b", strategy="sc",
                    reasoning_model="m", knobs={})
    complete_run(db, r1, final_answer="x", confidence=0.5,
                 tokens_used=10, elapsed_s=0.1)
    rows = list_runs(db, conversation_id=cid)
    assert len(rows) == 2
    assert rows[0]["created_at"] >= rows[1]["created_at"]  # DESC

    only_sc = list_runs(db, conversation_id=cid, strategy="sc")
    assert len(only_sc) == 1 and only_sc[0]["id"] == r2

    only_done = list_runs(db, conversation_id=cid, status="completed")
    assert len(only_done) == 1 and only_done[0]["id"] == r1
