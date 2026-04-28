# Real Reasoning Algorithms + FastAPI Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current single-call "reasoning modes" with real orchestrated algorithms (ToT, Self-Consistency, Reflexion, Multi-Agent Debate), persist every step to SQLite, expose the whole pipeline as a FastAPI service streaming structured events over SSE, and rewire the existing Gradio UI as a thin client of that API.

**Architecture:** SQLite-backed persistence layer (3 tables: conversations, runs, events) → in-process EventBus that persists then fans out → ReasoningStrategy ABC with registry of 7 implementations (4 real algorithms + 3 single-call wrappers) → thin Reasoner orchestrator → FastAPI server with SSE streaming → Gradio handlers rewired to consume the API.

**Tech Stack:** Python 3.10+, SQLite (stdlib), Pydantic v2, FastAPI, uvicorn, httpx, asyncio, pytest, pytest-asyncio, existing Groq SDK.

**Spec reference:** `docs/superpowers/specs/2026-04-26-real-reasoning-algorithms-design.md`

---

## Phase 0 — Dependencies and config

### Task 0.1: Add dependencies

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Add new dependencies to requirements.txt**

Append (preserving existing pinned packages):

```
fastapi>=0.110.0
uvicorn[standard]>=0.27.0
httpx>=0.27.0
pytest-asyncio>=0.23.0
```

Pydantic v2 is already pulled by `groq` and `gradio>=4`, no explicit pin needed.

- [ ] **Step 2: Install**

Run: `pip install -r requirements.txt`
Expected: all packages install cleanly, no resolver conflicts.

- [ ] **Step 3: Commit**

```bash
git add requirements.txt
git commit -m "deps: add fastapi, uvicorn, httpx, pytest-asyncio for Spec 1"
```

---

### Task 0.2: Add Spec 1 settings

**Files:**
- Modify: `src/config/settings.py`

- [ ] **Step 1: Read existing settings**

Run: `cat src/config/settings.py` to see the `AppConfig` shape and existing field style (env var loading pattern, defaults).

- [ ] **Step 2: Add new settings to AppConfig**

Inside `AppConfig` (preserve existing fields):

```python
# Spec 1 — backend persistence + concurrency
DB_PATH: str = os.getenv("DB_PATH", "./data/reasoning.db")
LLM_CONCURRENCY: int = int(os.getenv("LLM_CONCURRENCY", "8"))
DEFAULT_TOKEN_BUDGET: int = int(os.getenv("DEFAULT_TOKEN_BUDGET", "50000"))
DEFAULT_EVALUATOR_MODEL: str = os.getenv("DEFAULT_EVALUATOR_MODEL", "llama-3.1-8b-instant")
LLM_CALL_TIMEOUT_S: int = int(os.getenv("LLM_CALL_TIMEOUT_S", "60"))
RUN_TIMEOUT_S: int = int(os.getenv("RUN_TIMEOUT_S", "600"))
API_HOST: str = os.getenv("API_HOST", "127.0.0.1")
API_PORT: int = int(os.getenv("API_PORT", "8000"))
```

- [ ] **Step 3: Add `data/` to .gitignore**

Append to `.gitignore`:

```
data/
*.db
*.db-shm
*.db-wal
```

- [ ] **Step 4: Verify imports still work**

Run: `python -c "from src.config.settings import AppConfig; print(AppConfig.DB_PATH)"`
Expected: prints `./data/reasoning.db`.

- [ ] **Step 5: Commit**

```bash
git add src/config/settings.py .gitignore
git commit -m "config: add Spec 1 settings (DB_PATH, LLM_CONCURRENCY, budgets, timeouts)"
```

---

## Phase 1 — Storage

### Task 1.1: Migration runner + connection module

**Files:**
- Create: `src/storage/__init__.py`
- Create: `src/storage/db.py`
- Create: `src/storage/migrations/0001_init.sql`
- Create: `tests/storage/__init__.py`
- Create: `tests/storage/test_db.py`

- [ ] **Step 1: Write the failing test**

Create `tests/storage/test_db.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/storage/test_db.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.storage'`.

- [ ] **Step 3: Create the migration SQL**

Create `src/storage/migrations/0001_init.sql`:

```sql
CREATE TABLE conversations (
    id          TEXT PRIMARY KEY,
    created_at  REAL NOT NULL,
    title       TEXT,
    metadata    TEXT
);

CREATE TABLE runs (
    id                TEXT PRIMARY KEY,
    conversation_id   TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    created_at        REAL NOT NULL,
    completed_at      REAL,
    status            TEXT NOT NULL,
    strategy          TEXT NOT NULL,
    reasoning_model   TEXT NOT NULL,
    evaluator_model   TEXT,
    query             TEXT NOT NULL,
    knobs             TEXT NOT NULL,
    final_answer      TEXT,
    confidence        REAL,
    tokens_used       INTEGER DEFAULT 0,
    elapsed_s         REAL,
    error             TEXT
);

CREATE TABLE events (
    id           TEXT PRIMARY KEY,
    run_id       TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    seq          INTEGER NOT NULL,
    ts           REAL NOT NULL,
    type         TEXT NOT NULL,
    payload      TEXT NOT NULL,
    UNIQUE(run_id, seq)
);

CREATE INDEX idx_runs_conv ON runs(conversation_id, created_at DESC);
CREATE INDEX idx_runs_status ON runs(status);
CREATE INDEX idx_events_run_seq ON events(run_id, seq);
```

- [ ] **Step 4: Implement db.py**

Create `src/storage/__init__.py` (empty file).

Create `src/storage/db.py`:

```python
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
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/storage/test_db.py -v`
Expected: 3 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add src/storage/__init__.py src/storage/db.py src/storage/migrations/0001_init.sql tests/storage/__init__.py tests/storage/test_db.py
git commit -m "feat(storage): SQLite connection + migration runner + 0001_init schema"
```

---

### Task 1.2: DAO — conversations and runs

**Files:**
- Create: `src/storage/dao.py`
- Create: `tests/storage/test_dao.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/storage/test_dao.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/storage/test_dao.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.storage.dao'`.

- [ ] **Step 3: Implement dao.py**

Create `src/storage/dao.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/storage/test_dao.py -v`
Expected: 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/storage/dao.py tests/storage/test_dao.py
git commit -m "feat(storage): DAO for conversations + runs (CRUD, filters, status transitions)"
```

---

## Phase 2 — Events and event bus

### Task 2.1: Pydantic event models

**Files:**
- Create: `src/core/events.py`
- Create: `tests/core/__init__.py`
- Create: `tests/core/test_events.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/core/test_events.py`:

```python
import json
import pytest
from src.core.events import (
    ReasoningEvent, StrategyResult,
    RunStarted, RunCompleted, RunFailed, FinalAnswer,
    ThoughtGenerated, BranchScored, BeamPruned,
    SampleGenerated, AnswerExtracted, VoteTallied,
    AttemptGenerated, AttemptJudged, AgentSpoke, JudgeVerdict,
    new_event,
)


def test_new_event_assigns_id_and_ts():
    e = new_event(run_id="r1", type="RunStarted", payload={"strategy": "tot"})
    assert e.run_id == "r1"
    assert e.type == "RunStarted"
    assert isinstance(e.event_id, str) and len(e.event_id) >= 32
    assert e.ts > 0
    assert e.payload == {"strategy": "tot"}


def test_event_serialises_to_json_round_trip():
    e = new_event(run_id="r1", type="BranchScored",
                  payload={"node_id": "n1", "score": 0.9, "rationale": "ok"})
    blob = e.model_dump_json()
    restored = ReasoningEvent.model_validate_json(blob)
    assert restored.payload["score"] == 0.9


def test_strategy_result_required_fields():
    sr = StrategyResult(final_answer="42", confidence=0.8,
                        tokens_used=100, elapsed_s=1.0, trace_summary={})
    assert sr.confidence == 0.8


def test_concrete_event_helpers_set_type():
    assert RunStarted(run_id="r", payload={}).type == "RunStarted"
    assert FinalAnswer(run_id="r", payload={"text": "x"}).type == "FinalAnswer"
    assert BeamPruned(run_id="r", payload={"depth": 1, "kept": []}).type == "BeamPruned"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/core/test_events.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.core.events'`.

- [ ] **Step 3: Implement events.py**

Create `tests/core/__init__.py` (empty).

Create `src/core/events.py`:

```python
"""Pydantic models for streamed reasoning events + final result.

Every concrete event is a thin subclass that hardcodes `type`. This keeps
the wire format flat (one JSON envelope per event) while letting strategies
construct events with `XYZ(run_id=..., payload=...)` instead of fiddly
type strings.
"""
import time
import uuid
from typing import Any
from pydantic import BaseModel, Field


def _new_event_id() -> str:
    return uuid.uuid4().hex


class ReasoningEvent(BaseModel):
    event_id: str = Field(default_factory=_new_event_id)
    run_id: str
    type: str
    ts: float = Field(default_factory=time.time)
    payload: dict[str, Any] = Field(default_factory=dict)


class StrategyResult(BaseModel):
    final_answer: str
    confidence: float
    tokens_used: int
    elapsed_s: float
    trace_summary: dict[str, Any] = Field(default_factory=dict)


def new_event(*, run_id: str, type: str, payload: dict) -> ReasoningEvent:
    return ReasoningEvent(run_id=run_id, type=type, payload=payload)


def _typed(name: str):
    """Factory that builds a thin subclass with a frozen `type` field."""
    class _T(ReasoningEvent):
        type: str = name
    _T.__name__ = name
    return _T


# Lifecycle
RunStarted = _typed("RunStarted")
RunCompleted = _typed("RunCompleted")
RunFailed = _typed("RunFailed")
TokenBudgetExceeded = _typed("TokenBudgetExceeded")
FinalAnswer = _typed("FinalAnswer")

# ToT
ThoughtGenerated = _typed("ThoughtGenerated")
BranchScored = _typed("BranchScored")
BeamPruned = _typed("BeamPruned")
BranchFailed = _typed("BranchFailed")

# Self-Consistency
SampleGenerated = _typed("SampleGenerated")
AnswerExtracted = _typed("AnswerExtracted")
VoteTallied = _typed("VoteTallied")
SampleFailed = _typed("SampleFailed")

# Reflexion
AttemptGenerated = _typed("AttemptGenerated")
AttemptJudged = _typed("AttemptJudged")
CritiqueGenerated = _typed("CritiqueGenerated")
IterationFailed = _typed("IterationFailed")
TerminatedEarly = _typed("TerminatedEarly")

# Debate
AgentSpoke = _typed("AgentSpoke")
AgentFailed = _typed("AgentFailed")
JudgeVerdict = _typed("JudgeVerdict")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/core/test_events.py -v`
Expected: 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/core/events.py tests/core/__init__.py tests/core/test_events.py
git commit -m "feat(core): Pydantic event schema + StrategyResult + concrete event types"
```

---

### Task 2.2: EventBus — persist then fan out

**Files:**
- Create: `src/core/event_bus.py`
- Create: `tests/core/test_event_bus.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/core/test_event_bus.py`:

```python
import asyncio
import json
import pytest
from src.storage.db import open_db, run_migrations
from src.storage.dao import create_conversation, create_run
from src.core.event_bus import EventBus
from src.core.events import RunStarted, BranchScored, RunCompleted


@pytest.fixture
def db(tmp_path):
    conn = open_db(str(tmp_path / "t.db"))
    run_migrations(conn)
    yield conn
    conn.close()


@pytest.fixture
def seeded_run(db):
    cid = create_conversation(db)
    rid = create_run(db, conversation_id=cid, query="q", strategy="tot",
                     reasoning_model="m", knobs={})
    return rid


@pytest.mark.asyncio
async def test_publish_persists_with_monotonic_seq(db, seeded_run):
    bus = EventBus(db)
    await bus.publish(seeded_run, RunStarted(run_id=seeded_run, payload={}))
    await bus.publish(seeded_run, BranchScored(run_id=seeded_run,
                                               payload={"node_id": "n", "score": 0.5}))

    rows = db.execute(
        "SELECT seq, type, payload FROM events WHERE run_id=? ORDER BY seq",
        (seeded_run,)
    ).fetchall()
    assert [r["seq"] for r in rows] == [1, 2]
    assert rows[0]["type"] == "RunStarted"
    assert json.loads(rows[1]["payload"])["score"] == 0.5


@pytest.mark.asyncio
async def test_subscribers_receive_events(db, seeded_run):
    bus = EventBus(db)
    received = []
    queue = bus.subscribe(seeded_run)

    async def consumer():
        for _ in range(2):
            evt = await queue.get()
            received.append(evt.type)

    task = asyncio.create_task(consumer())
    await asyncio.sleep(0)  # let consumer attach
    await bus.publish(seeded_run, RunStarted(run_id=seeded_run, payload={}))
    await bus.publish(seeded_run, RunCompleted(run_id=seeded_run, payload={}))
    await asyncio.wait_for(task, timeout=1.0)
    assert received == ["RunStarted", "RunCompleted"]


@pytest.mark.asyncio
async def test_seq_continues_after_restart(db, seeded_run):
    bus1 = EventBus(db)
    await bus1.publish(seeded_run, RunStarted(run_id=seeded_run, payload={}))
    await bus1.publish(seeded_run, RunStarted(run_id=seeded_run, payload={}))

    # New bus instance simulates server restart
    bus2 = EventBus(db)
    await bus2.publish(seeded_run, RunCompleted(run_id=seeded_run, payload={}))
    seqs = [r["seq"] for r in db.execute(
        "SELECT seq FROM events WHERE run_id=? ORDER BY seq", (seeded_run,)
    ).fetchall()]
    assert seqs == [1, 2, 3]


@pytest.mark.asyncio
async def test_unsubscribe_removes_queue(db, seeded_run):
    bus = EventBus(db)
    queue = bus.subscribe(seeded_run)
    bus.unsubscribe(seeded_run, queue)
    # Publishing after unsubscribe must not raise / not write to dropped queue
    await bus.publish(seeded_run, RunStarted(run_id=seeded_run, payload={}))
    assert queue.qsize() == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/core/test_event_bus.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.core.event_bus'`.

- [ ] **Step 3: Implement EventBus**

Create `src/core/event_bus.py`:

```python
"""Per-run event bus: persists each event to SQLite, then fans out to
in-memory asyncio.Queue subscribers. Durability before delivery so SSE
reconnect via Last-Event-ID can replay losslessly from the events table.
"""
import asyncio
import sqlite3
from collections import defaultdict
from src.core.events import ReasoningEvent


class EventBus:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self._subs: dict[str, list[asyncio.Queue]] = defaultdict(list)
        self._next_seq: dict[str, int] = {}
        self._lock = asyncio.Lock()

    def _seq_for(self, run_id: str) -> int:
        if run_id not in self._next_seq:
            row = self.conn.execute(
                "SELECT COALESCE(MAX(seq), 0) FROM events WHERE run_id=?",
                (run_id,),
            ).fetchone()
            self._next_seq[run_id] = (row[0] or 0) + 1
        seq = self._next_seq[run_id]
        self._next_seq[run_id] = seq + 1
        return seq

    async def publish(self, run_id: str, event: ReasoningEvent) -> None:
        async with self._lock:
            seq = self._seq_for(run_id)
            self.conn.execute(
                "INSERT INTO events (id, run_id, seq, ts, type, payload) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (event.event_id, run_id, seq, event.ts, event.type,
                 event.model_dump_json(include={"payload"})),
            )
            # Stash seq on the event object for SSE writer (transient attribute)
            event.__dict__["seq"] = seq

        for q in list(self._subs.get(run_id, [])):
            q.put_nowait(event)

    def subscribe(self, run_id: str) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._subs[run_id].append(q)
        return q

    def unsubscribe(self, run_id: str, queue: asyncio.Queue) -> None:
        if run_id in self._subs and queue in self._subs[run_id]:
            self._subs[run_id].remove(queue)
            if not self._subs[run_id]:
                del self._subs[run_id]

    def replay(self, run_id: str, after_seq: int = 0) -> list[dict]:
        """Read persisted events from SQLite for SSE replay."""
        rows = self.conn.execute(
            "SELECT id, seq, ts, type, payload FROM events "
            "WHERE run_id=? AND seq > ? ORDER BY seq",
            (run_id, after_seq),
        ).fetchall()
        import json
        out = []
        for r in rows:
            payload = json.loads(r["payload"]).get("payload", {})
            out.append({
                "event_id": r["id"], "seq": r["seq"], "ts": r["ts"],
                "type": r["type"], "payload": payload, "run_id": run_id,
            })
        return out
```

- [ ] **Step 4: Add pytest-asyncio config**

Create or modify `pytest.ini` (project root):

```ini
[pytest]
asyncio_mode = auto
testpaths = tests
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/core/test_event_bus.py -v`
Expected: 4 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add src/core/event_bus.py tests/core/test_event_bus.py pytest.ini
git commit -m "feat(core): EventBus with durability-first persistence + asyncio fan-out"
```

---

## Phase 3 — Async Groq client + evaluator

### Task 3.1: FakeGroqClient test fixture

**Files:**
- Create: `tests/fakes/__init__.py`
- Create: `tests/fakes/groq.py`

- [ ] **Step 1: Implement the fake**

Create `tests/fakes/__init__.py` (empty).

Create `tests/fakes/groq.py`:

```python
"""Scripted async Groq client for tests. Returns objects shaped like the
real Groq SDK's `ChatCompletion` (only the fields our code reads).
"""
import json
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class _Usage:
    total_tokens: int = 100


@dataclass
class _Message:
    content: str


@dataclass
class _Choice:
    message: _Message


@dataclass
class FakeChatCompletion:
    choices: list[_Choice]
    usage: _Usage = field(default_factory=_Usage)


class FakeGroqClient:
    """
    `scripted` is either:
      - a list of str | dict — popped per call. dict items are returned as
        JSON strings (for JSON-mode calls).
      - a callable taking the messages list, returning str | dict.
    """
    def __init__(self, scripted):
        self.scripted = scripted
        self.calls: list[dict] = []
        self.sem = None  # strategies access .sem on real client; tests no-op

    async def acall(self, messages: list[dict], *, model: str,
                    temperature: float = 0.7, max_tokens: int = 4000,
                    json_mode: bool = False, tokens_used: int = 100) -> FakeChatCompletion:
        self.calls.append({
            "messages": messages, "model": model, "temperature": temperature,
            "max_tokens": max_tokens, "json_mode": json_mode,
        })
        if callable(self.scripted):
            nxt = self.scripted(messages)
        else:
            if not self.scripted:
                raise RuntimeError("FakeGroqClient: scripted list exhausted")
            nxt = self.scripted.pop(0)

        content = json.dumps(nxt) if isinstance(nxt, dict) else nxt
        return FakeChatCompletion(
            choices=[_Choice(message=_Message(content=content))],
            usage=_Usage(total_tokens=tokens_used),
        )
```

- [ ] **Step 2: Sanity-check the fake**

Run: `python -c "from tests.fakes.groq import FakeGroqClient; import asyncio; c = FakeGroqClient(['hi']); r = asyncio.run(c.acall([], model='m')); print(r.choices[0].message.content)"`
Expected: prints `hi`.

- [ ] **Step 3: Commit**

```bash
git add tests/fakes/__init__.py tests/fakes/groq.py
git commit -m "test: FakeGroqClient for deterministic strategy tests"
```

---

### Task 3.2: Async GroqClient with semaphore + JSON mode

**Files:**
- Modify: `src/api/groq_client.py`
- Create: `tests/api/__init__.py`
- Create: `tests/api/test_groq_client.py`

- [ ] **Step 1: Read existing client**

Run: `cat src/api/groq_client.py` to see the existing `GroqClientManager` shape and how it wraps the SDK.

- [ ] **Step 2: Write the failing test**

Create `tests/api/__init__.py` (empty).

Create `tests/api/test_groq_client.py`:

```python
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.api.groq_client import AsyncGroqClient


@pytest.fixture
def fake_sdk_response():
    msg = MagicMock(); msg.content = "hello"
    choice = MagicMock(); choice.message = msg
    completion = MagicMock(); completion.choices = [choice]
    completion.usage.total_tokens = 50
    return completion


@pytest.mark.asyncio
async def test_acall_returns_completion(fake_sdk_response):
    client = AsyncGroqClient(api_key="k", concurrency=4)
    with patch.object(client._sdk.chat.completions, "create",
                      AsyncMock(return_value=fake_sdk_response)):
        result = await client.acall(
            messages=[{"role": "user", "content": "hi"}],
            model="llama-3.1-8b-instant",
        )
    assert result.choices[0].message.content == "hello"
    assert result.usage.total_tokens == 50


@pytest.mark.asyncio
async def test_acall_json_mode_passes_response_format(fake_sdk_response):
    client = AsyncGroqClient(api_key="k", concurrency=4)
    create = AsyncMock(return_value=fake_sdk_response)
    with patch.object(client._sdk.chat.completions, "create", create):
        await client.acall(messages=[], model="m", json_mode=True)
    kwargs = create.call_args.kwargs
    assert kwargs["response_format"] == {"type": "json_object"}


@pytest.mark.asyncio
async def test_concurrency_semaphore_bounds_inflight():
    client = AsyncGroqClient(api_key="k", concurrency=2)
    inflight = 0
    peak = 0

    async def fake_create(**kw):
        nonlocal inflight, peak
        inflight += 1
        peak = max(peak, inflight)
        await asyncio.sleep(0.05)
        inflight -= 1
        return MagicMock(choices=[MagicMock(message=MagicMock(content=""))],
                         usage=MagicMock(total_tokens=1))

    with patch.object(client._sdk.chat.completions, "create",
                      side_effect=fake_create):
        await asyncio.gather(*[
            client.acall(messages=[], model="m") for _ in range(6)
        ])
    assert peak <= 2
```

- [ ] **Step 3: Run test to verify it fails**

Run: `pytest tests/api/test_groq_client.py -v`
Expected: FAIL with `ImportError: cannot import name 'AsyncGroqClient'`.

- [ ] **Step 4: Add AsyncGroqClient**

Append to `src/api/groq_client.py` (preserve existing `GroqClientManager` — Gradio still uses it during the transition):

```python
import asyncio
from groq import AsyncGroq
from src.config.settings import AppConfig


class AsyncGroqClient:
    """Async Groq wrapper with global concurrency cap + JSON-mode helper.

    Distinct from GroqClientManager (sync, used by legacy Reasoner path).
    Spec 1 backend uses this exclusively.
    """
    def __init__(self, *, api_key: str, concurrency: int = 8,
                 timeout_s: int = 60):
        self._sdk = AsyncGroq(api_key=api_key, timeout=timeout_s)
        self.sem = asyncio.Semaphore(concurrency)

    async def acall(self, *, messages: list[dict], model: str,
                    temperature: float = 0.7, max_tokens: int = 4000,
                    json_mode: bool = False):
        kwargs = dict(messages=messages, model=model,
                      temperature=temperature, max_tokens=max_tokens)
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        async with self.sem:
            return await self._sdk.chat.completions.create(**kwargs)


def make_async_client() -> AsyncGroqClient:
    return AsyncGroqClient(
        api_key=AppConfig.GROQ_API_KEY,
        concurrency=AppConfig.LLM_CONCURRENCY,
        timeout_s=AppConfig.LLM_CALL_TIMEOUT_S,
    )
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/api/test_groq_client.py -v`
Expected: 3 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add src/api/groq_client.py tests/api/__init__.py tests/api/test_groq_client.py
git commit -m "feat(api): AsyncGroqClient with semaphore + JSON-mode helper"
```

---

### Task 3.3: Evaluator — JSON-mode helpers per algorithm

**Files:**
- Create: `src/core/evaluator.py`
- Create: `tests/core/test_evaluator.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/core/test_evaluator.py`:

```python
import pytest
from src.core.evaluator import Evaluator, ScoreResult, ExtractResult, JudgeResult, DebateVerdict
from tests.fakes.groq import FakeGroqClient


@pytest.mark.asyncio
async def test_score_thought_parses_value_and_why():
    fake = FakeGroqClient([{"value": 0.82, "why": "logical step"}])
    ev = Evaluator(fake, model="ev-1")
    res = await ev.score_thought(problem="2+2", path=["thought"])
    assert isinstance(res, ScoreResult)
    assert res.value == 0.82
    assert res.why == "logical step"
    assert fake.calls[0]["json_mode"] is True


@pytest.mark.asyncio
async def test_score_thought_clamps_out_of_range():
    fake = FakeGroqClient([{"value": 1.5, "why": "x"}])
    ev = Evaluator(fake, model="ev-1")
    res = await ev.score_thought(problem="q", path=["t"])
    assert res.value == 1.0


@pytest.mark.asyncio
async def test_extract_answer_returns_canonical():
    fake = FakeGroqClient([{"answer": "The answer is 42.", "canonical": "42"}])
    ev = Evaluator(fake, model="ev-1")
    res = await ev.extract_answer(problem="q", sample="reasoning... 42")
    assert res.answer.endswith("42.")
    assert res.canonical == "42"


@pytest.mark.asyncio
async def test_judge_returns_score_and_issues():
    fake = FakeGroqClient([{"score": 0.6, "issues": ["unclear", "missing step"]}])
    ev = Evaluator(fake, model="ev-1")
    res = await ev.judge(problem="q", attempt="some answer")
    assert res.score == 0.6
    assert res.issues == ["unclear", "missing step"]


@pytest.mark.asyncio
async def test_judge_debate_returns_full_verdict():
    fake = FakeGroqClient([{
        "winner": "Analyst", "confidence": 0.75,
        "rationale": "stronger reasoning",
        "synthesis": "final answer text",
    }])
    ev = Evaluator(fake, model="ev-1")
    res = await ev.judge_debate(problem="q", transcripts={"Analyst": ["a"], "Skeptic": ["s"]})
    assert res.winner == "Analyst"
    assert res.confidence == 0.75
    assert res.synthesis.startswith("final")


@pytest.mark.asyncio
async def test_invalid_json_raises_evaluator_error():
    fake = FakeGroqClient(["not json at all"])
    ev = Evaluator(fake, model="ev-1")
    from src.core.evaluator import EvaluatorError
    with pytest.raises(EvaluatorError):
        await ev.score_thought(problem="q", path=["t"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/core/test_evaluator.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.core.evaluator'`.

- [ ] **Step 3: Implement evaluator**

Create `src/core/evaluator.py`:

```python
"""LLM-as-judge wrappers. Every method calls the evaluator model with
JSON mode and parses the result against a Pydantic schema. Used by all
four real strategies."""
import json
from pydantic import BaseModel, Field
from typing import Any


class EvaluatorError(Exception):
    """Raised when the evaluator returns malformed JSON or violates contract."""


class ScoreResult(BaseModel):
    value: float = Field(ge=0.0, le=1.0)
    why: str = ""


class ExtractResult(BaseModel):
    answer: str
    canonical: str


class JudgeResult(BaseModel):
    score: float = Field(ge=0.0, le=1.0)
    issues: list[str] = Field(default_factory=list)


class DebateVerdict(BaseModel):
    winner: str
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str = ""
    synthesis: str


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


class Evaluator:
    def __init__(self, client, model: str):
        self.client = client
        self.model = model

    async def _json_call(self, system: str, user: str) -> dict:
        resp = await self.client.acall(
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
            model=self.model, temperature=0.0, json_mode=True,
        )
        raw = resp.choices[0].message.content
        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            raise EvaluatorError(f"evaluator returned non-JSON: {raw!r}") from e

    async def score_thought(self, *, problem: str, path: list[str]) -> ScoreResult:
        system = (
            "You score partial reasoning steps. Output strict JSON: "
            '{"value": <float 0..1>, "why": "<one sentence>"}. '
            "value=1 means clearly on track, value=0 means dead end."
        )
        user = f"Problem:\n{problem}\n\nReasoning so far:\n" + "\n→ ".join(path)
        raw = await self._json_call(system, user)
        try:
            raw["value"] = _clamp01(float(raw.get("value", 0.0)))
            return ScoreResult(**raw)
        except Exception as e:
            raise EvaluatorError(f"bad ScoreResult: {raw!r}") from e

    async def extract_answer(self, *, problem: str, sample: str) -> ExtractResult:
        system = (
            "Extract the final answer from a reasoning trace. Output JSON: "
            '{"answer": "<verbatim final answer>", "canonical": "<normalized>"}. '
            "canonical: lowercase, stripped, numbers as bare digits, no units."
        )
        user = f"Problem:\n{problem}\n\nReasoning trace:\n{sample}"
        raw = await self._json_call(system, user)
        try:
            return ExtractResult(**raw)
        except Exception as e:
            raise EvaluatorError(f"bad ExtractResult: {raw!r}") from e

    async def judge(self, *, problem: str, attempt: str) -> JudgeResult:
        system = (
            "Judge an answer's quality. Output JSON: "
            '{"score": <float 0..1>, "issues": ["<concrete issue>", ...]}. '
            "issues are specific, actionable problems the author could fix."
        )
        user = f"Problem:\n{problem}\n\nAnswer:\n{attempt}"
        raw = await self._json_call(system, user)
        try:
            raw["score"] = _clamp01(float(raw.get("score", 0.0)))
            raw.setdefault("issues", [])
            return JudgeResult(**raw)
        except Exception as e:
            raise EvaluatorError(f"bad JudgeResult: {raw!r}") from e

    async def judge_debate(self, *, problem: str,
                           transcripts: dict[str, list[str]]) -> DebateVerdict:
        system = (
            "Judge a multi-agent debate. Output JSON: "
            '{"winner": "<persona name|consensus>", "confidence": <0..1>, '
            '"rationale": "<paragraph>", "synthesis": "<final answer>"}. '
            "synthesis is what the user sees — write it well."
        )
        formatted = "\n\n".join(
            f"=== {p} ===\n" + "\n---\n".join(msgs)
            for p, msgs in transcripts.items()
        )
        user = f"Problem:\n{problem}\n\nDebate:\n{formatted}"
        raw = await self._json_call(system, user)
        try:
            raw["confidence"] = _clamp01(float(raw.get("confidence", 0.0)))
            return DebateVerdict(**raw)
        except Exception as e:
            raise EvaluatorError(f"bad DebateVerdict: {raw!r}") from e
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/core/test_evaluator.py -v`
Expected: 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/core/evaluator.py tests/core/test_evaluator.py
git commit -m "feat(core): Evaluator with JSON-mode helpers (score, extract, judge, judge_debate)"
```

---

## Phase 4 — Strategy base + registry

### Task 4.1: Strategy ABC + config + registry stub

**Files:**
- Create: `src/core/strategies/__init__.py`
- Create: `src/core/strategies/base.py`
- Create: `tests/core/strategies/__init__.py`
- Create: `tests/core/strategies/test_base.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/core/strategies/__init__.py` (empty).

Create `tests/core/strategies/test_base.py`:

```python
import pytest
from src.core.strategies.base import (
    StrategyConfig, ReasoningStrategy, BudgetExceeded, TokenAccountant,
)
from src.core.events import StrategyResult


def test_strategy_config_defaults():
    c = StrategyConfig(reasoning_model="m1", evaluator_model="e1")
    assert c.token_budget == 50_000
    assert c.temperature == 0.7
    assert c.max_tokens == 4000
    assert c.knobs == {}


def test_token_accountant_tracks_and_raises():
    acct = TokenAccountant(budget=200)
    acct.add(80)
    acct.add(100)
    assert acct.used == 180
    with pytest.raises(BudgetExceeded):
        acct.add(50)


@pytest.mark.asyncio
async def test_strategy_subclass_must_implement_run():
    class Bad(ReasoningStrategy):
        name = "bad"
    with pytest.raises(TypeError):
        Bad(client=None, evaluator=None,
            config=StrategyConfig(reasoning_model="m", evaluator_model="e"))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/core/strategies/test_base.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement base**

Create `src/core/strategies/__init__.py`:

```python
"""Strategy registry. Concrete strategies register themselves on import."""
from src.core.strategies.base import ReasoningStrategy, StrategyConfig, BudgetExceeded
from src.core.strategies.tot import ToTStrategy
from src.core.strategies.self_consistency import SelfConsistencyStrategy
from src.core.strategies.reflexion import ReflexionStrategy
from src.core.strategies.debate import DebateStrategy
from src.core.strategies.single_call import (
    CoTStrategy, AnalogicalStrategy, SimpleStrategy,
)

STRATEGY_REGISTRY: dict[str, type[ReasoningStrategy]] = {
    "tot": ToTStrategy,
    "sc": SelfConsistencyStrategy,
    "reflexion": ReflexionStrategy,
    "debate": DebateStrategy,
    "cot": CoTStrategy,
    "analogical": AnalogicalStrategy,
    "simple": SimpleStrategy,
}

__all__ = ["STRATEGY_REGISTRY", "ReasoningStrategy", "StrategyConfig", "BudgetExceeded"]
```

(Note: this `__init__.py` won't import cleanly until later tasks add the concrete strategies. That's fine — `test_base.py` imports from `base` directly. Run-time use of the registry is only wired in Phase 6.)

Create `src/core/strategies/base.py`:

```python
"""Strategy ABC + shared config + token-budget accountant."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncGenerator, Union
from src.core.events import ReasoningEvent, StrategyResult


class BudgetExceeded(Exception):
    pass


@dataclass
class StrategyConfig:
    reasoning_model: str
    evaluator_model: str | None = None
    temperature: float = 0.7
    max_tokens: int = 4000
    token_budget: int = 50_000
    knobs: dict = field(default_factory=dict)


class TokenAccountant:
    def __init__(self, budget: int):
        self.budget = budget
        self.used = 0

    def add(self, n: int) -> None:
        if self.used + n > self.budget:
            raise BudgetExceeded(f"budget {self.budget} exceeded "
                                 f"(would reach {self.used + n})")
        self.used += n


class ReasoningStrategy(ABC):
    name: str

    def __init__(self, *, client, evaluator, config: StrategyConfig,
                 run_id: str = ""):
        self.client = client
        self.evaluator = evaluator
        self.config = config
        self.run_id = run_id
        self.tokens = TokenAccountant(config.token_budget)

    @abstractmethod
    async def run(self, problem: str) -> AsyncGenerator[
        Union[ReasoningEvent, StrategyResult], None
    ]:
        """Yield events as they happen, end with a single StrategyResult."""
        if False:
            yield  # pragma: no cover (typing hack: marks as async gen)

    async def _call_reasoning(self, messages, **kw):
        """Wrap a reasoning-model call: track tokens, propagate budget."""
        resp = await self.client.acall(
            messages=messages, model=self.config.reasoning_model,
            temperature=kw.pop("temperature", self.config.temperature),
            max_tokens=kw.pop("max_tokens", self.config.max_tokens),
            **kw,
        )
        self.tokens.add(resp.usage.total_tokens)
        return resp.choices[0].message.content
```

- [ ] **Step 4: Run base tests to verify they pass**

Run: `pytest tests/core/strategies/test_base.py -v`
Expected: 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/core/strategies/__init__.py src/core/strategies/base.py tests/core/strategies/__init__.py tests/core/strategies/test_base.py
git commit -m "feat(strategies): ABC + StrategyConfig + TokenAccountant + registry stub"
```

(The strategies/__init__.py import will fail until Phase 5 lands the concretes — don't import it yet.)

---

## Phase 5 — Concrete strategies

### Task 5.1: Single-call wrapper strategies (CoT, Analogical, Simple)

**Files:**
- Create: `src/core/strategies/single_call.py`
- Create: `tests/core/strategies/test_single_call.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/core/strategies/test_single_call.py`:

```python
import pytest
from src.core.strategies.base import StrategyConfig
from src.core.strategies.single_call import CoTStrategy, AnalogicalStrategy, SimpleStrategy
from src.core.events import StrategyResult, FinalAnswer
from tests.fakes.groq import FakeGroqClient


@pytest.mark.parametrize("StratCls,name", [
    (CoTStrategy, "cot"), (AnalogicalStrategy, "analogical"), (SimpleStrategy, "simple"),
])
@pytest.mark.asyncio
async def test_single_call_yields_final_answer_then_result(StratCls, name):
    fake = FakeGroqClient(["the answer"])
    cfg = StrategyConfig(reasoning_model="m", evaluator_model=None)
    strat = StratCls(client=fake, evaluator=None, config=cfg, run_id="r")

    events = []
    result = None
    async for item in strat.run("q?"):
        if isinstance(item, StrategyResult):
            result = item
        else:
            events.append(item)

    assert strat.name == name
    assert any(e.type == "FinalAnswer" and e.payload["text"] == "the answer" for e in events)
    assert result is not None
    assert result.final_answer == "the answer"
    assert result.confidence == 1.0   # single-call: no scoring, full confidence
    assert result.tokens_used == 100
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/core/strategies/test_single_call.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement single_call.py**

Create `src/core/strategies/single_call.py`:

```python
"""Wrapper strategies for the three single-call modes (CoT, Analogical, Simple).

These exist so /runs is uniform across all 7 modes and the evaluation harness
in Spec 2 can benchmark orchestrated algos against unstructured prompting
with no special-case code paths.
"""
import time
from src.core.events import FinalAnswer, StrategyResult
from src.core.strategies.base import ReasoningStrategy


_PROMPTS = {
    "cot": "You are a careful reasoner. Think step by step before answering.",
    "analogical": ("You are a reasoner who solves problems by drawing analogies "
                   "to similar problems you've seen before. Surface the analogy explicitly."),
    "simple": "Answer concisely and directly.",
}


class _SingleCallBase(ReasoningStrategy):
    async def run(self, problem: str):
        t0 = time.time()
        messages = [
            {"role": "system", "content": _PROMPTS[self.name]},
            {"role": "user", "content": problem},
        ]
        text = await self._call_reasoning(messages)
        yield FinalAnswer(run_id=self.run_id,
                          payload={"text": text, "confidence": 1.0})
        yield StrategyResult(
            final_answer=text, confidence=1.0,
            tokens_used=self.tokens.used, elapsed_s=time.time() - t0,
            trace_summary={},
        )


class CoTStrategy(_SingleCallBase):
    name = "cot"


class AnalogicalStrategy(_SingleCallBase):
    name = "analogical"


class SimpleStrategy(_SingleCallBase):
    name = "simple"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/core/strategies/test_single_call.py -v`
Expected: 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/core/strategies/single_call.py tests/core/strategies/test_single_call.py
git commit -m "feat(strategies): CoT, Analogical, Simple single-call wrappers"
```

---

### Task 5.2: Self-Consistency strategy

**Files:**
- Create: `src/core/strategies/self_consistency.py`
- Create: `tests/core/strategies/test_self_consistency.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/core/strategies/test_self_consistency.py`:

```python
import pytest
from src.core.strategies.base import StrategyConfig
from src.core.strategies.self_consistency import SelfConsistencyStrategy
from src.core.evaluator import Evaluator
from src.core.events import StrategyResult
from tests.fakes.groq import FakeGroqClient


@pytest.mark.asyncio
async def test_sc_majority_vote_winner_and_share():
    # 5 reasoning samples, then 5 extract calls (JSON dicts)
    scripted = [
        "step a → 42", "step b → 42", "step c → 7", "step d → 42", "step e → 7",
        {"answer": "42", "canonical": "42"},
        {"answer": "42", "canonical": "42"},
        {"answer": "7",  "canonical": "7"},
        {"answer": "42", "canonical": "42"},
        {"answer": "7",  "canonical": "7"},
    ]
    fake = FakeGroqClient(scripted)
    cfg = StrategyConfig(reasoning_model="rm", evaluator_model="em",
                         knobs={"n_samples": 5})
    strat = SelfConsistencyStrategy(
        client=fake, evaluator=Evaluator(fake, model="em"),
        config=cfg, run_id="r",
    )

    events, result = [], None
    async for item in strat.run("q?"):
        if isinstance(item, StrategyResult):
            result = item
        else:
            events.append(item)

    vote = next(e for e in events if e.type == "VoteTallied")
    assert vote.payload["winner"] == "42"
    assert vote.payload["share"] == 0.6  # 3/5
    assert result.confidence == 0.6
    assert result.final_answer.endswith("42")


@pytest.mark.asyncio
async def test_sc_aborts_when_too_few_samples_survive():
    # all 5 reasoning calls return text fine, but 4 of 5 extracts return invalid
    # JSON → SampleFailed events, leaving only 1 valid sample
    from src.core.evaluator import EvaluatorError
    scripted = [
        "x", "x", "x", "x", "x",
        {"answer": "ok", "canonical": "ok"},
        "not json", "not json", "not json", "not json",
    ]
    fake = FakeGroqClient(scripted)
    cfg = StrategyConfig(reasoning_model="rm", evaluator_model="em",
                         knobs={"n_samples": 5})
    strat = SelfConsistencyStrategy(
        client=fake, evaluator=Evaluator(fake, model="em"),
        config=cfg, run_id="r",
    )
    events = [e async for e in strat.run("q?") if not isinstance(e, StrategyResult)]
    failed = [e for e in events if e.type == "SampleFailed"]
    assert len(failed) == 4
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/core/strategies/test_self_consistency.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement Self-Consistency**

Create `src/core/strategies/self_consistency.py`:

```python
"""Self-Consistency: sample N reasoning paths in parallel, extract canonical
answer from each, majority vote. Reference: Wang et al., 2022.
"""
import asyncio
import time
from collections import Counter
from src.core.events import (
    SampleGenerated, AnswerExtracted, VoteTallied, FinalAnswer,
    SampleFailed, StrategyResult,
)
from src.core.evaluator import EvaluatorError
from src.core.strategies.base import ReasoningStrategy


class SelfConsistencyStrategy(ReasoningStrategy):
    name = "sc"

    async def run(self, problem: str):
        t0 = time.time()
        n = self.config.knobs.get("n_samples", 5)
        sample_temp = self.config.knobs.get("sample_temperature", 0.9)

        # Stage 1: parallel reasoning samples
        async def one_sample():
            return await self._call_reasoning(
                messages=[
                    {"role": "system", "content":
                     "Think step by step. Show your reasoning, then state the final answer."},
                    {"role": "user", "content": problem},
                ],
                temperature=sample_temp,
            )

        samples = await asyncio.gather(
            *[one_sample() for _ in range(n)], return_exceptions=True
        )
        valid_samples: list[tuple[int, str]] = []
        for i, s in enumerate(samples):
            if isinstance(s, Exception):
                yield SampleFailed(run_id=self.run_id,
                                   payload={"sample_id": i, "error": str(s)})
                continue
            valid_samples.append((i, s))
            yield SampleGenerated(run_id=self.run_id,
                                  payload={"sample_id": i, "text": s})

        # Stage 2: parallel extraction
        async def extract(sample_text):
            return await self.evaluator.extract_answer(problem=problem, sample=sample_text)

        extracted_raw = await asyncio.gather(
            *[extract(s) for _, s in valid_samples], return_exceptions=True
        )
        extracted: list[tuple[int, str, str]] = []  # (sample_id, answer, canonical)
        for (sid, _), res in zip(valid_samples, extracted_raw):
            if isinstance(res, Exception):
                yield SampleFailed(run_id=self.run_id,
                                   payload={"sample_id": sid, "error": str(res)})
                continue
            extracted.append((sid, res.answer, res.canonical))
            yield AnswerExtracted(run_id=self.run_id, payload={
                "sample_id": sid, "answer": res.answer, "canonical": res.canonical,
            })

        if len(extracted) < 2:
            raise RuntimeError(f"self-consistency: only {len(extracted)} valid samples; aborting")

        # Stage 3: vote
        tally = Counter(c for _, _, c in extracted)
        winner, count = tally.most_common(1)[0]
        share = count / n
        yield VoteTallied(run_id=self.run_id, payload={
            "tally": dict(tally), "winner": winner, "share": share,
        })

        # Pick representative full sample for the winning canonical
        representative_sid = next(sid for sid, _, c in extracted if c == winner)
        representative_text = next(s for i, s in valid_samples if i == representative_sid)

        yield FinalAnswer(run_id=self.run_id, payload={
            "text": representative_text, "vote_share": share, "confidence": share,
        })
        yield StrategyResult(
            final_answer=representative_text, confidence=share,
            tokens_used=self.tokens.used, elapsed_s=time.time() - t0,
            trace_summary={"tally": dict(tally), "winner": winner},
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/core/strategies/test_self_consistency.py -v`
Expected: 2 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/core/strategies/self_consistency.py tests/core/strategies/test_self_consistency.py
git commit -m "feat(strategies): Self-Consistency (parallel sampling + canonical vote)"
```

---

### Task 5.3: Tree of Thoughts strategy

**Files:**
- Create: `src/core/strategies/tot.py`
- Create: `tests/core/strategies/test_tot.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/core/strategies/test_tot.py`:

```python
import pytest
from src.core.strategies.base import StrategyConfig
from src.core.strategies.tot import ToTStrategy
from src.core.evaluator import Evaluator
from src.core.events import StrategyResult
from tests.fakes.groq import FakeGroqClient


def _scripted_tree(branching, beam, depth):
    """Build a deterministic script: each thought-gen call returns N\\n-joined
    thoughts; each evaluator call returns a known score."""
    out = []
    # depth 1: 1 root call → branching thoughts; then `branching` eval calls
    out.append("\n".join(f"thought-d1-{i}" for i in range(branching)))
    out += [{"value": 0.9 - 0.1 * i, "why": ""} for i in range(branching)]
    # depth 2..depth: beam expansions
    for d in range(2, depth + 1):
        for b in range(beam):
            out.append("\n".join(f"thought-d{d}-b{b}-{i}" for i in range(branching)))
        out += [{"value": 0.9 - 0.05 * i, "why": ""} for i in range(beam * branching)]
    # synthesis
    out.append("FINAL")
    return out


@pytest.mark.asyncio
async def test_tot_runs_to_synthesis():
    fake = FakeGroqClient(_scripted_tree(branching=3, beam=2, depth=2))
    cfg = StrategyConfig(reasoning_model="rm", evaluator_model="em",
                         knobs={"branching_factor": 3, "beam_width": 2,
                                "max_depth": 2, "score_threshold": 0.99})
    strat = ToTStrategy(client=fake, evaluator=Evaluator(fake, model="em"),
                        config=cfg, run_id="r")
    events, result = [], None
    async for item in strat.run("solve x"):
        if isinstance(item, StrategyResult):
            result = item
        else:
            events.append(item)

    assert any(e.type == "BeamPruned" for e in events)
    pruned = [e for e in events if e.type == "BeamPruned"]
    assert all(len(e.payload["kept"]) <= 2 for e in pruned)
    assert any(e.type == "FinalAnswer" and e.payload["text"] == "FINAL" for e in events)
    assert result.final_answer == "FINAL"
    assert 0.0 <= result.confidence <= 1.0


@pytest.mark.asyncio
async def test_tot_early_stops_on_threshold():
    # depth 1 produces a 0.95 score → above threshold of 0.9
    scripted = [
        "t1\nt2\nt3",
        {"value": 0.95, "why": ""}, {"value": 0.4, "why": ""}, {"value": 0.4, "why": ""},
        "EARLY-FINAL",   # synthesis
    ]
    fake = FakeGroqClient(scripted)
    cfg = StrategyConfig(reasoning_model="rm", evaluator_model="em",
                         knobs={"branching_factor": 3, "beam_width": 2,
                                "max_depth": 5, "score_threshold": 0.9})
    strat = ToTStrategy(client=fake, evaluator=Evaluator(fake, model="em"),
                        config=cfg, run_id="r")
    events = [e async for e in strat.run("q") if not isinstance(e, StrategyResult)]
    pruned = [e for e in events if e.type == "BeamPruned"]
    assert len(pruned) == 1   # stopped after depth 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/core/strategies/test_tot.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement ToT**

Create `src/core/strategies/tot.py`:

```python
"""Tree of Thoughts: branch + score + prune to a beam, repeat to depth.
Reference: Yao et al., 2023.

Thought-generation calls return one thought per line (newline-separated).
"""
import asyncio
import time
import uuid
from dataclasses import dataclass, field
from src.core.events import (
    ThoughtGenerated, BranchScored, BeamPruned, BranchFailed, FinalAnswer,
    StrategyResult,
)
from src.core.strategies.base import ReasoningStrategy


@dataclass
class _Node:
    id: str
    text: str
    parent_id: str | None
    depth: int
    score: float = 0.0
    path: list[str] = field(default_factory=list)


class ToTStrategy(ReasoningStrategy):
    name = "tot"

    async def run(self, problem: str):
        t0 = time.time()
        bf = self.config.knobs.get("branching_factor", 3)
        max_depth = self.config.knobs.get("max_depth", 3)
        beam = self.config.knobs.get("beam_width", 2)
        threshold = self.config.knobs.get("score_threshold", 0.7)

        root = _Node(id="root", text="<problem>", parent_id=None,
                     depth=0, score=1.0, path=[])
        frontier = [root]

        for depth in range(1, max_depth + 1):
            children = await self._expand_frontier(problem, frontier, bf, depth)
            if not children:
                break

            scores = await asyncio.gather(*[
                self.evaluator.score_thought(problem=problem, path=c.path)
                for c in children
            ], return_exceptions=True)
            scored: list[_Node] = []
            for c, s in zip(children, scores):
                if isinstance(s, Exception):
                    yield BranchFailed(run_id=self.run_id,
                                       payload={"node_id": c.id, "error": str(s)})
                    continue
                c.score = s.value
                scored.append(c)
                yield BranchScored(run_id=self.run_id, payload={
                    "node_id": c.id, "score": s.value, "rationale": s.why,
                })

            if not scored:
                break

            scored.sort(key=lambda n: n.score, reverse=True)
            frontier = scored[:beam]
            yield BeamPruned(run_id=self.run_id, payload={
                "depth": depth, "kept": [n.id for n in frontier],
            })

            if frontier[0].score >= threshold:
                break

        if not frontier:
            raise RuntimeError("ToT: frontier empty before synthesis")

        best = frontier[0]
        synthesis = await self._call_reasoning(messages=[
            {"role": "system", "content":
             "Synthesize a final answer using the given reasoning path."},
            {"role": "user", "content":
             f"Problem:\n{problem}\n\nBest reasoning path:\n" + "\n→ ".join(best.path)},
        ])
        yield FinalAnswer(run_id=self.run_id, payload={
            "text": synthesis, "path": best.path, "confidence": best.score,
        })
        yield StrategyResult(
            final_answer=synthesis, confidence=best.score,
            tokens_used=self.tokens.used, elapsed_s=time.time() - t0,
            trace_summary={"best_path": best.path, "best_score": best.score},
        )

    async def _expand_frontier(self, problem, frontier, bf, depth):
        async def expand(node):
            text = await self._call_reasoning(messages=[
                {"role": "system", "content":
                 f"Generate {bf} distinct next reasoning steps. "
                 "Output one per line, no numbering."},
                {"role": "user", "content":
                 f"Problem:\n{problem}\n\nReasoning so far:\n" +
                 ("\n→ ".join(node.path) if node.path else "(start)")},
            ])
            thoughts = [t.strip() for t in text.splitlines() if t.strip()][:bf]
            return node, thoughts

        results = await asyncio.gather(*[expand(n) for n in frontier],
                                       return_exceptions=True)
        out: list[_Node] = []
        emitted = []
        for r in results:
            if isinstance(r, Exception):
                continue
            parent, thoughts = r
            for t in thoughts:
                child = _Node(id=uuid.uuid4().hex[:8], text=t,
                              parent_id=parent.id, depth=depth,
                              path=parent.path + [t])
                out.append(child)
                emitted.append(child)
        # Emit ThoughtGenerated for each (caller will yield through the generator)
        for c in emitted:
            # We can't yield from a non-generator helper; return list and let run() emit.
            pass
        # Strategy: collect children and yield events from run()
        self._pending_thoughts = emitted
        return emitted
```

Wait — `_expand_frontier` can't yield through `run()` cleanly with that pattern. Refactor: make `_expand_frontier` itself a regular function returning the children list, and have `run()` emit `ThoughtGenerated` after collecting them. Replace the trailing block of `_expand_frontier` (the `# Strategy: collect...` lines and `_pending_thoughts`) and update `run()` accordingly.

Update `run()` to emit `ThoughtGenerated` after `_expand_frontier`:

```python
        for depth in range(1, max_depth + 1):
            children = await self._expand_frontier(problem, frontier, bf, depth)
            for c in children:
                yield ThoughtGenerated(run_id=self.run_id, payload={
                    "node_id": c.id, "parent_id": c.parent_id,
                    "depth": c.depth, "text": c.text,
                })
            if not children:
                break
            # ... (rest unchanged)
```

And drop the dead `emitted = []`, `for c in emitted:`, `self._pending_thoughts = emitted` lines from `_expand_frontier`. Final `_expand_frontier` ends at `out.append(child)` block followed by `return out`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/core/strategies/test_tot.py -v`
Expected: 2 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/core/strategies/tot.py tests/core/strategies/test_tot.py
git commit -m "feat(strategies): Tree of Thoughts (branch + score + prune + synthesize)"
```

---

### Task 5.4: Reflexion strategy

**Files:**
- Create: `src/core/strategies/reflexion.py`
- Create: `tests/core/strategies/test_reflexion.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/core/strategies/test_reflexion.py`:

```python
import pytest
from src.core.strategies.base import StrategyConfig
from src.core.strategies.reflexion import ReflexionStrategy
from src.core.evaluator import Evaluator
from src.core.events import StrategyResult
from tests.fakes.groq import FakeGroqClient


@pytest.mark.asyncio
async def test_reflexion_terminates_on_threshold():
    scripted = [
        "first attempt",
        {"score": 0.9, "issues": []},   # judge: above threshold → stop
    ]
    fake = FakeGroqClient(scripted)
    cfg = StrategyConfig(reasoning_model="rm", evaluator_model="em",
                         knobs={"max_iterations": 3, "quality_threshold": 0.85})
    strat = ReflexionStrategy(
        client=fake, evaluator=Evaluator(fake, model="em"),
        config=cfg, run_id="r",
    )
    events, result = [], None
    async for item in strat.run("q"):
        if isinstance(item, StrategyResult):
            result = item
        else:
            events.append(item)

    assert any(e.type == "TerminatedEarly" and e.payload["reason"] == "threshold" for e in events)
    assert result.final_answer == "first attempt"
    assert result.confidence == 0.9


@pytest.mark.asyncio
async def test_reflexion_iterates_when_below_threshold():
    scripted = [
        "attempt 1",
        {"score": 0.3, "issues": ["wrong"]},   # judge iter 1
        "critique 1",
        "attempt 2",
        {"score": 0.95, "issues": []},         # judge iter 2 → stop
    ]
    fake = FakeGroqClient(scripted)
    cfg = StrategyConfig(reasoning_model="rm", evaluator_model="em",
                         knobs={"max_iterations": 3, "quality_threshold": 0.9,
                                "min_improvement": 0.01})
    strat = ReflexionStrategy(
        client=fake, evaluator=Evaluator(fake, model="em"),
        config=cfg, run_id="r",
    )
    events = [e async for e in strat.run("q") if not isinstance(e, StrategyResult)]
    attempts = [e for e in events if e.type == "AttemptGenerated"]
    assert len(attempts) == 2
    assert attempts[1].payload["text"] == "attempt 2"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/core/strategies/test_reflexion.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement Reflexion**

Create `src/core/strategies/reflexion.py`:

```python
"""Reflexion: iterative critique→refine. Reference: Shinn et al., 2023.

Sequential by design — each iteration depends on the previous attempt's
critique. Three calls per non-terminal iteration: judge, critique, refine.
"""
import time
from src.core.events import (
    AttemptGenerated, AttemptJudged, CritiqueGenerated, IterationFailed,
    TerminatedEarly, FinalAnswer, StrategyResult,
)
from src.core.strategies.base import ReasoningStrategy


class ReflexionStrategy(ReasoningStrategy):
    name = "reflexion"

    async def run(self, problem: str):
        t0 = time.time()
        max_iter = self.config.knobs.get("max_iterations", 3)
        threshold = self.config.knobs.get("quality_threshold", 0.85)
        min_improve = self.config.knobs.get("min_improvement", 0.05)

        attempt = await self._call_reasoning(messages=[
            {"role": "system", "content": "Solve the problem carefully."},
            {"role": "user", "content": problem},
        ])
        yield AttemptGenerated(run_id=self.run_id,
                               payload={"iter": 0, "text": attempt})

        prev_score = 0.0
        last_score = 0.0
        terminated_iter = 0
        for it in range(1, max_iter + 1):
            judged = await self.evaluator.judge(problem=problem, attempt=attempt)
            yield AttemptJudged(run_id=self.run_id, payload={
                "iter": it - 1, "score": judged.score, "issues": judged.issues,
            })
            last_score = judged.score
            terminated_iter = it - 1

            if judged.score >= threshold:
                yield TerminatedEarly(run_id=self.run_id, payload={
                    "reason": "threshold", "score": judged.score,
                })
                break
            if it > 1 and (judged.score - prev_score) < min_improve:
                yield TerminatedEarly(run_id=self.run_id, payload={
                    "reason": "plateau", "score": judged.score,
                })
                break

            try:
                critique = await self._call_reasoning(messages=[
                    {"role": "system", "content":
                     "You are a reviewer. Write critique addressing each issue."},
                    {"role": "user", "content":
                     f"Problem:\n{problem}\n\nAnswer:\n{attempt}\n\n"
                     f"Issues:\n- " + "\n- ".join(judged.issues)},
                ])
                yield CritiqueGenerated(run_id=self.run_id,
                                        payload={"iter": it, "text": critique})

                attempt = await self._call_reasoning(messages=[
                    {"role": "system", "content":
                     "Refine the previous answer using the critique."},
                    {"role": "user", "content":
                     f"Problem:\n{problem}\n\nPrevious answer:\n{attempt}\n\n"
                     f"Critique:\n{critique}"},
                ])
                yield AttemptGenerated(run_id=self.run_id,
                                       payload={"iter": it, "text": attempt})
            except Exception as e:
                yield IterationFailed(run_id=self.run_id,
                                      payload={"iter": it, "error": str(e)})
                break

            prev_score = judged.score

        yield FinalAnswer(run_id=self.run_id, payload={
            "text": attempt, "confidence": last_score, "iterations": terminated_iter,
        })
        yield StrategyResult(
            final_answer=attempt, confidence=last_score,
            tokens_used=self.tokens.used, elapsed_s=time.time() - t0,
            trace_summary={"final_score": last_score, "iterations": terminated_iter},
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/core/strategies/test_reflexion.py -v`
Expected: 2 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/core/strategies/reflexion.py tests/core/strategies/test_reflexion.py
git commit -m "feat(strategies): Reflexion (iterative critique→refine with judge gating)"
```

---

### Task 5.5: Multi-Agent Debate strategy

**Files:**
- Create: `src/core/strategies/debate.py`
- Create: `tests/core/strategies/test_debate.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/core/strategies/test_debate.py`:

```python
import pytest
from src.core.strategies.base import StrategyConfig
from src.core.strategies.debate import DebateStrategy
from src.core.evaluator import Evaluator
from src.core.events import StrategyResult
from tests.fakes.groq import FakeGroqClient


@pytest.mark.asyncio
async def test_debate_two_agents_three_rounds_then_judge():
    scripted = [
        # Round 1: 2 openings (Analyst, Skeptic)
        "Analyst opening", "Skeptic opening",
        # Round 2: 2 responses
        "Analyst r2", "Skeptic r2",
        # Round 3: 2 responses
        "Analyst r3", "Skeptic r3",
        # Judge verdict (JSON)
        {"winner": "Analyst", "confidence": 0.7,
         "rationale": "stronger arguments", "synthesis": "FINAL TEXT"},
    ]
    fake = FakeGroqClient(scripted)
    cfg = StrategyConfig(reasoning_model="rm", evaluator_model="em",
                         knobs={"n_rounds": 3,
                                "personas": ["Analyst", "Skeptic"]})
    strat = DebateStrategy(client=fake, evaluator=Evaluator(fake, model="em"),
                           config=cfg, run_id="r")
    events, result = [], None
    async for item in strat.run("q?"):
        if isinstance(item, StrategyResult):
            result = item
        else:
            events.append(item)

    spoken = [e for e in events if e.type == "AgentSpoke"]
    assert len(spoken) == 6
    assert {e.payload["agent"] for e in spoken} == {"Analyst", "Skeptic"}
    assert any(e.type == "JudgeVerdict" for e in events)
    assert result.final_answer == "FINAL TEXT"
    assert result.confidence == 0.7
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/core/strategies/test_debate.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement Debate**

Create `src/core/strategies/debate.py`:

```python
"""Multi-Agent Debate: distinct personas exchange responses across rounds,
judge synthesizes the final answer. Reference: Du et al., 2023.

Within-round: parallel (each agent answers independently).
Cross-round: sequential (each round needs prior responses).
"""
import asyncio
import time
from src.core.events import (
    AgentSpoke, AgentFailed, JudgeVerdict, FinalAnswer, StrategyResult,
)
from src.core.strategies.base import ReasoningStrategy


_PERSONA_PROMPTS = {
    "Analyst": ("You are the Analyst. Reason rigorously and constructively. "
                "Build the strongest case for a correct answer."),
    "Skeptic": ("You are the Skeptic. Probe assumptions and surface flaws. "
                "Challenge weak reasoning."),
}


def _persona_system(name: str) -> str:
    return _PERSONA_PROMPTS.get(name, f"You are the {name}. Argue your position carefully.")


class DebateStrategy(ReasoningStrategy):
    name = "debate"

    async def run(self, problem: str):
        t0 = time.time()
        personas: list[str] = self.config.knobs.get("personas", ["Analyst", "Skeptic"])
        n_rounds = self.config.knobs.get("n_rounds", 3)
        transcripts: dict[str, list[str]] = {p: [] for p in personas}

        # Round 1 — parallel openings
        async def open_one(persona):
            return await self._call_reasoning(messages=[
                {"role": "system", "content": _persona_system(persona)},
                {"role": "user", "content": f"Problem:\n{problem}\n\nGive your opening position."},
            ])

        opens = await asyncio.gather(*[open_one(p) for p in personas],
                                     return_exceptions=True)
        for p, msg in zip(personas, opens):
            if isinstance(msg, Exception):
                yield AgentFailed(run_id=self.run_id, payload={
                    "round": 1, "agent": p, "error": str(msg),
                })
                continue
            transcripts[p].append(msg)
            yield AgentSpoke(run_id=self.run_id, payload={
                "round": 1, "agent": p, "text": msg,
            })

        # Rounds 2..N — each agent sees other personas' last messages
        for r in range(2, n_rounds + 1):
            async def respond_one(persona):
                others_last = [transcripts[other][-1]
                               for other in personas
                               if other != persona and transcripts[other]]
                own_history = "\n---\n".join(transcripts[persona])
                others_text = "\n\n".join(others_last) or "(no rebuttal yet)"
                return await self._call_reasoning(messages=[
                    {"role": "system", "content": _persona_system(persona)},
                    {"role": "user", "content":
                     f"Problem:\n{problem}\n\nYour previous statements:\n{own_history}\n\n"
                     f"Other agents' latest:\n{others_text}\n\nRespond."},
                ])

            responses = await asyncio.gather(*[respond_one(p) for p in personas],
                                             return_exceptions=True)
            spoke_this_round = 0
            for p, msg in zip(personas, responses):
                if isinstance(msg, Exception):
                    yield AgentFailed(run_id=self.run_id, payload={
                        "round": r, "agent": p, "error": str(msg),
                    })
                    continue
                transcripts[p].append(msg)
                spoke_this_round += 1
                yield AgentSpoke(run_id=self.run_id, payload={
                    "round": r, "agent": p, "text": msg,
                })
            if spoke_this_round == 0:
                raise RuntimeError(f"debate: all agents failed in round {r}")

        # Judge
        verdict = await self.evaluator.judge_debate(problem=problem,
                                                    transcripts=transcripts)
        yield JudgeVerdict(run_id=self.run_id, payload={
            "winner": verdict.winner, "confidence": verdict.confidence,
            "rationale": verdict.rationale,
        })
        yield FinalAnswer(run_id=self.run_id, payload={
            "text": verdict.synthesis, "confidence": verdict.confidence,
            "winner": verdict.winner,
        })
        yield StrategyResult(
            final_answer=verdict.synthesis, confidence=verdict.confidence,
            tokens_used=self.tokens.used, elapsed_s=time.time() - t0,
            trace_summary={"winner": verdict.winner, "rounds": n_rounds},
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/core/strategies/test_debate.py -v`
Expected: 1 test PASS.

- [ ] **Step 5: Verify the registry imports cleanly now**

Run: `python -c "from src.core.strategies import STRATEGY_REGISTRY; print(sorted(STRATEGY_REGISTRY))"`
Expected: prints `['analogical', 'cot', 'debate', 'reflexion', 'sc', 'simple', 'tot']`.

- [ ] **Step 6: Commit**

```bash
git add src/core/strategies/debate.py tests/core/strategies/test_debate.py
git commit -m "feat(strategies): Multi-Agent Debate (parallel within round + judge synthesis)"
```

---

## Phase 6 — Reasoner orchestrator

### Task 6.1: Refactor Reasoner to drive strategies + emit lifecycle events

**Files:**
- Modify: `src/core/reasoner.py`
- Create: `tests/core/test_reasoner.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/core/test_reasoner.py`:

```python
import pytest
from src.storage.db import open_db, run_migrations
from src.storage.dao import create_conversation, create_run, get_run
from src.core.event_bus import EventBus
from src.core.evaluator import Evaluator
from src.core.reasoner import AsyncReasoner
from src.core.strategies.base import StrategyConfig
from tests.fakes.groq import FakeGroqClient


@pytest.fixture
def db(tmp_path):
    conn = open_db(str(tmp_path / "t.db"))
    run_migrations(conn)
    yield conn
    conn.close()


@pytest.mark.asyncio
async def test_reasoner_runs_simple_strategy_and_completes_run(db):
    cid = create_conversation(db)
    rid = create_run(db, conversation_id=cid, query="hi", strategy="simple",
                     reasoning_model="m", knobs={})
    fake = FakeGroqClient(["hello back"])
    bus = EventBus(db)
    reasoner = AsyncReasoner(client=fake, bus=bus, store=db)

    cfg = StrategyConfig(reasoning_model="m", evaluator_model=None)
    await reasoner.run(run_id=rid, problem="hi", strategy_name="simple", config=cfg)

    row = get_run(db, rid)
    assert row["status"] == "completed"
    assert row["final_answer"] == "hello back"
    assert row["confidence"] == 1.0

    types = [r["type"] for r in db.execute(
        "SELECT type FROM events WHERE run_id=? ORDER BY seq", (rid,)
    ).fetchall()]
    assert types[0] == "RunStarted"
    assert "FinalAnswer" in types
    assert types[-1] == "RunCompleted"


@pytest.mark.asyncio
async def test_reasoner_marks_run_failed_on_strategy_exception(db):
    cid = create_conversation(db)
    rid = create_run(db, conversation_id=cid, query="hi", strategy="simple",
                     reasoning_model="m", knobs={})
    # FakeGroqClient with empty scripted list → strategy will raise on first call
    fake = FakeGroqClient([])
    bus = EventBus(db)
    reasoner = AsyncReasoner(client=fake, bus=bus, store=db)

    cfg = StrategyConfig(reasoning_model="m", evaluator_model=None)
    with pytest.raises(Exception):
        await reasoner.run(run_id=rid, problem="hi", strategy_name="simple", config=cfg)

    row = get_run(db, rid)
    assert row["status"] == "failed"
    assert row["error"]
    types = [r["type"] for r in db.execute(
        "SELECT type FROM events WHERE run_id=? ORDER BY seq", (rid,)
    ).fetchall()]
    assert types[-1] == "RunFailed"


@pytest.mark.asyncio
async def test_reasoner_uses_evaluator_for_orchestrated_strategies(db):
    cid = create_conversation(db)
    rid = create_run(db, conversation_id=cid, query="hi", strategy="reflexion",
                     reasoning_model="m", evaluator_model="e", knobs={})
    fake = FakeGroqClient([
        "first", {"score": 0.99, "issues": []},   # judge above threshold → stops
    ])
    bus = EventBus(db)
    reasoner = AsyncReasoner(client=fake, bus=bus, store=db)

    cfg = StrategyConfig(reasoning_model="m", evaluator_model="e",
                         knobs={"max_iterations": 2, "quality_threshold": 0.9})
    await reasoner.run(run_id=rid, problem="hi", strategy_name="reflexion", config=cfg)
    assert get_run(db, rid)["status"] == "completed"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/core/test_reasoner.py -v`
Expected: FAIL — current `reasoner.py` exports `AdvancedReasoner`, not `AsyncReasoner`.

- [ ] **Step 3: Add AsyncReasoner alongside the legacy class**

Append to `src/core/reasoner.py` (preserve existing `AdvancedReasoner` until Phase 8 deletes the legacy path):

```python
import time
from src.core.event_bus import EventBus
from src.core.events import RunStarted, RunCompleted, RunFailed, StrategyResult
from src.core.evaluator import Evaluator
from src.core.strategies import STRATEGY_REGISTRY
from src.core.strategies.base import StrategyConfig
from src.storage import dao
from src.config.settings import AppConfig


class AsyncReasoner:
    """Spec 1 orchestrator. Drives a strategy, persists lifecycle, fans out
    events via the bus. Replaces AdvancedReasoner.generate_response over time.
    """
    def __init__(self, *, client, bus: EventBus, store):
        self.client = client
        self.bus = bus
        self.store = store

    async def run(self, *, run_id: str, problem: str, strategy_name: str,
                  config: StrategyConfig) -> None:
        if strategy_name not in STRATEGY_REGISTRY:
            err = f"unknown strategy: {strategy_name}"
            dao.fail_run(self.store, run_id, error=err)
            await self.bus.publish(run_id, RunFailed(run_id=run_id, payload={"error": err}))
            raise ValueError(err)

        evaluator = None
        if config.evaluator_model:
            evaluator = Evaluator(self.client, model=config.evaluator_model)

        strat_cls = STRATEGY_REGISTRY[strategy_name]
        strat = strat_cls(client=self.client, evaluator=evaluator,
                          config=config, run_id=run_id)

        await self.bus.publish(run_id, RunStarted(run_id=run_id, payload={
            "strategy": strategy_name, "model": config.reasoning_model,
            "evaluator_model": config.evaluator_model, "knobs": config.knobs,
        }))

        result: StrategyResult | None = None
        try:
            async for item in strat.run(problem):
                if isinstance(item, StrategyResult):
                    result = item
                else:
                    await self.bus.publish(run_id, item)
        except Exception as e:
            dao.fail_run(self.store, run_id, error=str(e))
            await self.bus.publish(run_id, RunFailed(run_id=run_id,
                                                    payload={"error": str(e)}))
            raise

        if result is None:
            err = f"strategy {strategy_name} produced no StrategyResult"
            dao.fail_run(self.store, run_id, error=err)
            await self.bus.publish(run_id, RunFailed(run_id=run_id, payload={"error": err}))
            raise RuntimeError(err)

        dao.complete_run(
            self.store, run_id,
            final_answer=result.final_answer, confidence=result.confidence,
            tokens_used=result.tokens_used, elapsed_s=result.elapsed_s,
        )
        await self.bus.publish(run_id, RunCompleted(run_id=run_id, payload={
            "final_answer": result.final_answer, "confidence": result.confidence,
            "tokens_used": result.tokens_used, "elapsed_s": result.elapsed_s,
            "trace_summary": result.trace_summary,
        }))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/core/test_reasoner.py -v`
Expected: 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/core/reasoner.py tests/core/test_reasoner.py
git commit -m "feat(core): AsyncReasoner orchestrator (lifecycle events + status persistence)"
```

---

## Phase 7 — FastAPI server

### Task 7.1: Schemas + meta routes (/health, /modes, /models)

**Files:**
- Create: `src/api/schemas.py`
- Create: `src/api/routes/__init__.py`
- Create: `src/api/routes/meta.py`
- Create: `src/api/server.py`
- Create: `tests/api/test_meta.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/api/test_meta.py`:

```python
import pytest
from httpx import AsyncClient, ASGITransport
from src.api.server import build_app


@pytest.fixture
async def client(tmp_path, monkeypatch):
    monkeypatch.setattr("src.config.settings.AppConfig.DB_PATH", str(tmp_path / "t.db"))
    app = build_app(api_key="test-key")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_returns_ok(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_modes_returns_seven_strategies(client):
    r = await client.get("/modes")
    assert r.status_code == 200
    modes = {m["name"] for m in r.json()["modes"]}
    assert modes == {"tot", "sc", "reflexion", "debate", "cot", "analogical", "simple"}


@pytest.mark.asyncio
async def test_models_returns_groq_list(client):
    r = await client.get("/models")
    assert r.status_code == 200
    assert isinstance(r.json()["models"], list)
    assert len(r.json()["models"]) > 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/api/test_meta.py -v`
Expected: FAIL — modules don't exist.

- [ ] **Step 3: Implement schemas + meta + server skeleton**

Create `src/api/schemas.py`:

```python
"""Pydantic request/response models for the FastAPI surface."""
from typing import Optional, Any
from pydantic import BaseModel, Field


class StartRunRequest(BaseModel):
    conversation_id: Optional[str] = None
    query: str
    strategy: str
    reasoning_model: str
    evaluator_model: Optional[str] = None
    knobs: dict[str, Any] = Field(default_factory=dict)
    token_budget: Optional[int] = None
    temperature: float = 0.7
    max_tokens: int = 4000


class StartRunResponse(BaseModel):
    run_id: str
    status: str = "running"


class RunRow(BaseModel):
    id: str
    conversation_id: str
    created_at: float
    completed_at: Optional[float]
    status: str
    strategy: str
    reasoning_model: str
    evaluator_model: Optional[str]
    query: str
    knobs: dict
    final_answer: Optional[str]
    confidence: Optional[float]
    tokens_used: int
    elapsed_s: Optional[float]
    error: Optional[str]


class CreateConversationRequest(BaseModel):
    title: Optional[str] = None


class ErrorResponse(BaseModel):
    error: str
    code: str
```

Create `src/api/routes/__init__.py` (empty).

Create `src/api/routes/meta.py`:

```python
from fastapi import APIRouter, Request
from src.core.strategies import STRATEGY_REGISTRY
from src.config.constants import ModelConfig

router = APIRouter()


@router.get("/health")
async def health(request: Request):
    db = request.app.state.db
    db.execute("SELECT 1").fetchone()
    return {"status": "ok"}


_MODE_DEFAULTS = {
    "tot": {"branching_factor": 3, "max_depth": 3, "beam_width": 2,
            "score_threshold": 0.7},
    "sc": {"n_samples": 5, "sample_temperature": 0.9, "agreement_threshold": 0.6},
    "reflexion": {"max_iterations": 3, "quality_threshold": 0.85,
                  "min_improvement": 0.05},
    "debate": {"personas": ["Analyst", "Skeptic"], "n_rounds": 3},
    "cot": {}, "analogical": {}, "simple": {},
}


@router.get("/modes")
async def list_modes():
    return {"modes": [
        {"name": name, "default_knobs": _MODE_DEFAULTS.get(name, {}),
         "single_call": name in {"cot", "analogical", "simple"}}
        for name in sorted(STRATEGY_REGISTRY.keys())
    ]}


@router.get("/models")
async def list_models():
    models = getattr(ModelConfig, "AVAILABLE_MODELS", None) or []
    if not models:
        # Fallback: scrape constants by convention
        models = [v for k, v in vars(ModelConfig).items()
                  if isinstance(v, str) and "/" not in v and not k.startswith("_")
                  and k.isupper()]
    return {"models": [{"id": m} for m in models]}
```

Create `src/api/server.py`:

```python
"""FastAPI app factory + lifespan: opens DB, runs migrations, attaches
EventBus and AsyncGroqClient to app.state. Keeps app construction
testable (no module-level side effects)."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.storage.db import open_db, run_migrations
from src.core.event_bus import EventBus
from src.api.groq_client import AsyncGroqClient
from src.config.settings import AppConfig
from src.api.routes import meta


def build_app(*, api_key: str | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.db = open_db(AppConfig.DB_PATH)
        run_migrations(app.state.db)
        app.state.bus = EventBus(app.state.db)
        app.state.client = AsyncGroqClient(
            api_key=api_key or AppConfig.GROQ_API_KEY,
            concurrency=AppConfig.LLM_CONCURRENCY,
            timeout_s=AppConfig.LLM_CALL_TIMEOUT_S,
        )
        yield
        app.state.db.close()

    app = FastAPI(title="Reasoning API", lifespan=lifespan)
    app.include_router(meta.router)
    return app


app = build_app()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/api/test_meta.py -v`
Expected: 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/api/schemas.py src/api/routes/__init__.py src/api/routes/meta.py src/api/server.py tests/api/test_meta.py
git commit -m "feat(api): FastAPI app factory + meta routes (/health, /modes, /models)"
```

---

### Task 7.2: Conversations route

**Files:**
- Create: `src/api/routes/conversations.py`
- Create: `tests/api/test_conversations.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/api/test_conversations.py`:

```python
import pytest
from httpx import AsyncClient, ASGITransport
from src.api.server import build_app


@pytest.fixture
async def client(tmp_path, monkeypatch):
    monkeypatch.setattr("src.config.settings.AppConfig.DB_PATH", str(tmp_path / "t.db"))
    app = build_app(api_key="k")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
        yield ac


@pytest.mark.asyncio
async def test_create_and_list_conversation(client):
    r = await client.post("/conversations", json={"title": "first"})
    assert r.status_code == 200
    cid = r.json()["id"]

    r2 = await client.get("/conversations")
    assert any(c["id"] == cid and c["title"] == "first" for c in r2.json()["conversations"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/api/test_conversations.py -v`
Expected: FAIL with 404 (route not registered).

- [ ] **Step 3: Implement conversations route**

Create `src/api/routes/conversations.py`:

```python
from fastapi import APIRouter, Request
from src.api.schemas import CreateConversationRequest
from src.storage import dao

router = APIRouter()


@router.post("/conversations")
async def create_conversation(req: CreateConversationRequest, request: Request):
    cid = dao.create_conversation(request.app.state.db, title=req.title)
    return {"id": cid, "title": req.title}


@router.get("/conversations")
async def list_conversations(request: Request, limit: int = 100, offset: int = 0):
    rows = dao.list_conversations(request.app.state.db, limit=limit, offset=offset)
    return {"conversations": [dict(r) for r in rows]}
```

Register in `src/api/server.py` `build_app`:

```python
from src.api.routes import meta, conversations
# ...
app.include_router(meta.router)
app.include_router(conversations.router)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/api/test_conversations.py -v`
Expected: 1 test PASS.

- [ ] **Step 5: Commit**

```bash
git add src/api/routes/conversations.py src/api/server.py tests/api/test_conversations.py
git commit -m "feat(api): /conversations create + list endpoints"
```

---

### Task 7.3: Runs route — POST/GET/DELETE/list

**Files:**
- Create: `src/api/routes/runs.py`
- Create: `tests/api/test_runs.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/api/test_runs.py`:

```python
import asyncio
import pytest
from unittest.mock import patch
from httpx import AsyncClient, ASGITransport
from src.api.server import build_app
from tests.fakes.groq import FakeGroqClient


@pytest.fixture
async def client(tmp_path, monkeypatch):
    monkeypatch.setattr("src.config.settings.AppConfig.DB_PATH", str(tmp_path / "t.db"))
    fake = FakeGroqClient(["hello world"])
    with patch("src.api.server.AsyncGroqClient", return_value=fake):
        app = build_app(api_key="k")
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
            yield ac, fake


@pytest.mark.asyncio
async def test_post_runs_returns_id_and_runs_to_completion(client):
    ac, _ = client
    cid = (await ac.post("/conversations", json={})).json()["id"]
    r = await ac.post("/runs", json={
        "conversation_id": cid, "query": "hi", "strategy": "simple",
        "reasoning_model": "m",
    })
    assert r.status_code == 200
    rid = r.json()["run_id"]

    # Wait for the background task to complete
    for _ in range(20):
        row = (await ac.get(f"/runs/{rid}")).json()
        if row["status"] != "running":
            break
        await asyncio.sleep(0.05)

    assert row["status"] == "completed"
    assert row["final_answer"] == "hello world"


@pytest.mark.asyncio
async def test_get_run_404_for_unknown(client):
    ac, _ = client
    r = await ac.get("/runs/no-such-id")
    assert r.status_code == 404
    assert r.json()["code"] == "RUN_NOT_FOUND"


@pytest.mark.asyncio
async def test_list_runs_filters_by_conversation(client):
    ac, _ = client
    cid = (await ac.post("/conversations", json={})).json()["id"]
    await ac.post("/runs", json={
        "conversation_id": cid, "query": "x", "strategy": "simple",
        "reasoning_model": "m",
    })
    r = await ac.get("/runs", params={"conversation_id": cid})
    assert r.status_code == 200
    assert len(r.json()["runs"]) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/api/test_runs.py -v`
Expected: FAIL with 404 (route not registered).

- [ ] **Step 3: Implement runs route**

Create `src/api/routes/runs.py`:

```python
import asyncio
import json
from typing import Optional
from fastapi import APIRouter, Request, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from src.api.schemas import StartRunRequest
from src.storage import dao
from src.core.reasoner import AsyncReasoner
from src.core.strategies import STRATEGY_REGISTRY
from src.core.strategies.base import StrategyConfig
from src.config.settings import AppConfig

router = APIRouter()


def _err(code: str, msg: str, status: int = 400):
    return JSONResponse(status_code=status, content={"error": msg, "code": code})


@router.post("/runs")
async def start_run(req: StartRunRequest, request: Request):
    if req.strategy not in STRATEGY_REGISTRY:
        return _err("INVALID_STRATEGY", f"unknown strategy {req.strategy}")

    db = request.app.state.db
    cid = req.conversation_id
    if not cid:
        cid = dao.create_conversation(db)

    eval_model = req.evaluator_model
    if eval_model is None and req.strategy in {"tot", "sc", "reflexion", "debate"}:
        eval_model = AppConfig.DEFAULT_EVALUATOR_MODEL

    rid = dao.create_run(
        db, conversation_id=cid, query=req.query, strategy=req.strategy,
        reasoning_model=req.reasoning_model, evaluator_model=eval_model,
        knobs=req.knobs,
    )

    cfg = StrategyConfig(
        reasoning_model=req.reasoning_model,
        evaluator_model=eval_model,
        temperature=req.temperature,
        max_tokens=req.max_tokens,
        token_budget=req.token_budget or AppConfig.DEFAULT_TOKEN_BUDGET,
        knobs=req.knobs,
    )
    reasoner = AsyncReasoner(client=request.app.state.client,
                             bus=request.app.state.bus, store=db)

    async def _run_in_background():
        try:
            await asyncio.wait_for(
                reasoner.run(run_id=rid, problem=req.query,
                             strategy_name=req.strategy, config=cfg),
                timeout=AppConfig.RUN_TIMEOUT_S,
            )
        except asyncio.TimeoutError:
            dao.fail_run(db, rid, error="run timeout exceeded")
        except Exception:
            pass  # AsyncReasoner already persists failure + emits RunFailed

    asyncio.create_task(_run_in_background())
    return {"run_id": rid, "status": "running"}


@router.get("/runs/{run_id}")
async def get_run(run_id: str, request: Request):
    row = dao.get_run(request.app.state.db, run_id)
    if not row:
        return _err("RUN_NOT_FOUND", f"no run {run_id}", status=404)
    d = dict(row)
    d["knobs"] = json.loads(d["knobs"]) if d["knobs"] else {}
    return d


@router.delete("/runs/{run_id}")
async def cancel_run(run_id: str, request: Request):
    db = request.app.state.db
    row = dao.get_run(db, run_id)
    if not row:
        return _err("RUN_NOT_FOUND", f"no run {run_id}", status=404)
    if row["status"] == "running":
        dao.cancel_run(db, run_id)
    return {"status": "aborted"}


@router.get("/runs")
async def list_runs(request: Request,
                    conversation_id: Optional[str] = None,
                    status: Optional[str] = None,
                    strategy: Optional[str] = None,
                    limit: int = Query(100, ge=1, le=500),
                    offset: int = Query(0, ge=0)):
    rows = dao.list_runs(request.app.state.db, conversation_id=conversation_id,
                         status=status, strategy=strategy,
                         limit=limit, offset=offset)
    out = []
    for r in rows:
        d = dict(r)
        d["knobs"] = json.loads(d["knobs"]) if d["knobs"] else {}
        out.append(d)
    return {"runs": out}
```

Register in `src/api/server.py`:

```python
from src.api.routes import meta, conversations, runs
# ...
app.include_router(runs.router)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/api/test_runs.py -v`
Expected: 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/api/routes/runs.py src/api/server.py tests/api/test_runs.py
git commit -m "feat(api): /runs POST/GET/DELETE/list with background execution"
```

---

### Task 7.4: SSE endpoint — live stream + Last-Event-ID replay

**Files:**
- Modify: `src/api/routes/runs.py`
- Create: `tests/api/test_sse.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/api/test_sse.py`:

```python
import asyncio
import json
import pytest
from unittest.mock import patch
from httpx import AsyncClient, ASGITransport
from src.api.server import build_app
from tests.fakes.groq import FakeGroqClient


def parse_sse(text: str) -> list[dict]:
    """Parse a text/event-stream blob into [{id, event, data}, ...]."""
    out = []
    cur = {}
    for line in text.splitlines():
        if not line.strip() and cur:
            if "data" in cur:
                cur["data"] = json.loads(cur["data"])
            out.append(cur); cur = {}
            continue
        if line.startswith(":"):  # heartbeat comment
            continue
        if ":" in line:
            k, _, v = line.partition(":")
            cur[k.strip()] = v.lstrip()
    return out


@pytest.fixture
async def client(tmp_path, monkeypatch):
    monkeypatch.setattr("src.config.settings.AppConfig.DB_PATH", str(tmp_path / "t.db"))
    fake = FakeGroqClient(["streamed answer"])
    with patch("src.api.server.AsyncGroqClient", return_value=fake):
        app = build_app(api_key="k")
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
            yield ac


@pytest.mark.asyncio
async def test_sse_returns_completed_run_events(client):
    cid = (await client.post("/conversations", json={})).json()["id"]
    rid = (await client.post("/runs", json={
        "conversation_id": cid, "query": "hi", "strategy": "simple",
        "reasoning_model": "m",
    })).json()["run_id"]

    # Wait until the run is done so replay path is exercised
    for _ in range(20):
        row = (await client.get(f"/runs/{rid}")).json()
        if row["status"] != "running":
            break
        await asyncio.sleep(0.05)

    r = await client.get(f"/runs/{rid}/events")
    assert r.status_code == 200
    events = parse_sse(r.text)
    types = [e["event"] for e in events]
    assert "RunStarted" in types
    assert "FinalAnswer" in types
    assert types[-1] in {"RunCompleted", "RunFailed"}


@pytest.mark.asyncio
async def test_sse_last_event_id_skips_replayed(client):
    cid = (await client.post("/conversations", json={})).json()["id"]
    rid = (await client.post("/runs", json={
        "conversation_id": cid, "query": "hi", "strategy": "simple",
        "reasoning_model": "m",
    })).json()["run_id"]

    for _ in range(20):
        if (await client.get(f"/runs/{rid}")).json()["status"] != "running":
            break
        await asyncio.sleep(0.05)

    r = await client.get(f"/runs/{rid}/events", headers={"Last-Event-ID": "1"})
    events = parse_sse(r.text)
    seqs = [int(e["id"]) for e in events]
    assert all(s > 1 for s in seqs)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/api/test_sse.py -v`
Expected: FAIL with 404 (route not present).

- [ ] **Step 3: Add SSE handler to runs route**

Add to `src/api/routes/runs.py`:

```python
import json
import asyncio
from fastapi.responses import StreamingResponse


def _sse_format(*, seq: int, event_type: str, data: dict) -> str:
    return f"id: {seq}\nevent: {event_type}\ndata: {json.dumps(data)}\n\n"


@router.get("/runs/{run_id}/events")
async def stream_events(run_id: str, request: Request):
    db = request.app.state.db
    bus = request.app.state.bus
    if not dao.get_run(db, run_id):
        return _err("RUN_NOT_FOUND", f"no run {run_id}", status=404)

    last_event_id = request.headers.get("Last-Event-ID")
    after_seq = int(last_event_id) if last_event_id and last_event_id.isdigit() else 0

    async def gen():
        # 1) Replay persisted events past last_event_id
        for evt in bus.replay(run_id, after_seq=after_seq):
            yield _sse_format(seq=evt["seq"], event_type=evt["type"], data=evt)

        # 2) If run already terminal, end stream
        row = dao.get_run(db, run_id)
        if row and row["status"] != "running":
            return

        # 3) Otherwise subscribe and stream until terminal event
        queue = bus.subscribe(run_id)
        try:
            while True:
                try:
                    evt = await asyncio.wait_for(queue.get(), timeout=15.0)
                except asyncio.TimeoutError:
                    yield ": ping\n\n"
                    continue
                seq = evt.__dict__.get("seq", 0)
                yield _sse_format(seq=seq, event_type=evt.type, data={
                    "event_id": evt.event_id, "seq": seq, "ts": evt.ts,
                    "type": evt.type, "payload": evt.payload, "run_id": run_id,
                })
                if evt.type in {"RunCompleted", "RunFailed"}:
                    return
        finally:
            bus.unsubscribe(run_id, queue)

    return StreamingResponse(gen(), media_type="text/event-stream")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/api/test_sse.py -v`
Expected: 2 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/api/routes/runs.py tests/api/test_sse.py
git commit -m "feat(api): SSE /runs/:id/events with Last-Event-ID replay + heartbeat"
```

---

## Phase 8 — Gradio adapter + all-in-one launcher

### Task 8.1: ReasoningAPIClient

**Files:**
- Create: `src/ui/api_client.py`
- Create: `tests/ui/__init__.py`
- Create: `tests/ui/test_api_client.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/ui/__init__.py` (empty).

Create `tests/ui/test_api_client.py`:

```python
import asyncio
import pytest
from unittest.mock import patch
from httpx import AsyncClient, ASGITransport
from src.api.server import build_app
from src.ui.api_client import ReasoningAPIClient
from tests.fakes.groq import FakeGroqClient


@pytest.fixture
async def app_and_client(tmp_path, monkeypatch):
    monkeypatch.setattr("src.config.settings.AppConfig.DB_PATH", str(tmp_path / "t.db"))
    fake = FakeGroqClient(["hi", "hi"])
    with patch("src.api.server.AsyncGroqClient", return_value=fake):
        app = build_app(api_key="k")
        # Mount the in-process app behind an httpx transport
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
            client = ReasoningAPIClient(base_url="http://test", http_client=http)
            yield client


@pytest.mark.asyncio
async def test_start_run_and_stream_to_final(app_and_client):
    client = app_and_client
    run_id = await client.start_run(
        query="hi", strategy="simple", reasoning_model="m",
    )
    assert isinstance(run_id, str)

    types = []
    async for evt in client.stream_events(run_id):
        types.append(evt["type"])
        if evt["type"] in {"RunCompleted", "RunFailed"}:
            break
    assert "FinalAnswer" in types
    assert types[-1] == "RunCompleted"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/ui/test_api_client.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement client**

Create `src/ui/api_client.py`:

```python
"""Async HTTP client wrapping the FastAPI surface. Used by the Gradio
adapter; will be replaced by the Next.js frontend in Spec 1.5.
"""
import json
from typing import Any, AsyncGenerator, Optional
import httpx


class ReasoningAPIClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000",
                 http_client: Optional[httpx.AsyncClient] = None,
                 timeout_s: int = 600):
        self.base = base_url.rstrip("/")
        self._http = http_client or httpx.AsyncClient(timeout=timeout_s)
        self._owns_http = http_client is None

    async def aclose(self):
        if self._owns_http:
            await self._http.aclose()

    async def start_run(self, *, query: str, strategy: str, reasoning_model: str,
                        conversation_id: Optional[str] = None,
                        evaluator_model: Optional[str] = None,
                        knobs: Optional[dict] = None,
                        token_budget: Optional[int] = None,
                        temperature: float = 0.7,
                        max_tokens: int = 4000) -> str:
        body = {
            "query": query, "strategy": strategy,
            "reasoning_model": reasoning_model,
            "conversation_id": conversation_id,
            "evaluator_model": evaluator_model,
            "knobs": knobs or {},
            "token_budget": token_budget,
            "temperature": temperature, "max_tokens": max_tokens,
        }
        body = {k: v for k, v in body.items() if v is not None}
        r = await self._http.post(f"{self.base}/runs", json=body)
        r.raise_for_status()
        return r.json()["run_id"]

    async def get_run(self, run_id: str) -> dict:
        r = await self._http.get(f"{self.base}/runs/{run_id}")
        r.raise_for_status()
        return r.json()

    async def stream_events(self, run_id: str,
                            last_event_id: Optional[int] = None
                            ) -> AsyncGenerator[dict[str, Any], None]:
        headers = {}
        if last_event_id is not None:
            headers["Last-Event-ID"] = str(last_event_id)
        async with self._http.stream("GET", f"{self.base}/runs/{run_id}/events",
                                     headers=headers) as r:
            r.raise_for_status()
            data_buf: list[str] = []
            event_type: Optional[str] = None
            event_id: Optional[str] = None
            async for line in r.aiter_lines():
                if not line.strip():
                    if data_buf and event_type:
                        try:
                            payload = json.loads("".join(data_buf))
                        except json.JSONDecodeError:
                            payload = {"raw": "".join(data_buf)}
                        yield {"type": event_type, "id": event_id,
                               **(payload if isinstance(payload, dict) else {})}
                    data_buf, event_type, event_id = [], None, None
                    continue
                if line.startswith(":"):
                    continue
                if line.startswith("id:"):
                    event_id = line[3:].strip()
                elif line.startswith("event:"):
                    event_type = line[6:].strip()
                elif line.startswith("data:"):
                    data_buf.append(line[5:].lstrip())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/ui/test_api_client.py -v`
Expected: 1 test PASS.

- [ ] **Step 5: Commit**

```bash
git add src/ui/api_client.py tests/ui/__init__.py tests/ui/test_api_client.py
git commit -m "feat(ui): ReasoningAPIClient (start_run + SSE event stream)"
```

---

### Task 8.2: Rewrite Gradio handlers to use API client

**Files:**
- Modify: `src/ui/handlers.py`

- [ ] **Step 1: Read existing handlers to find generate_response_handler**

Run: `grep -n "generate_response" src/ui/handlers.py` to identify the function and its signature.

- [ ] **Step 2: Replace the handler body**

Replace the existing `generate_response_handler` (and any related cache/critique paths it directly calls) with a version that drives the API client. Add at the top of `src/ui/handlers.py`:

```python
import asyncio
from src.ui.api_client import ReasoningAPIClient

_API_CLIENT: ReasoningAPIClient | None = None


def _get_client() -> ReasoningAPIClient:
    global _API_CLIENT
    if _API_CLIENT is None:
        from src.config.settings import AppConfig
        _API_CLIENT = ReasoningAPIClient(
            base_url=f"http://{AppConfig.API_HOST}:{AppConfig.API_PORT}"
        )
    return _API_CLIENT


def _render_event_inline(evt: dict) -> str:
    t = evt.get("type", "")
    payload = evt.get("payload", {})
    if t == "ThoughtGenerated":
        return f"\n\n*💭 {payload.get('text', '')[:200]}*"
    if t == "BranchScored":
        return f"\n\n*⭐ scored {payload.get('score', 0):.2f}: {payload.get('rationale', '')}*"
    if t == "BeamPruned":
        return f"\n\n*✂️ kept {len(payload.get('kept', []))} branches*"
    if t == "AgentSpoke":
        return f"\n\n**{payload.get('agent', 'agent')}** ({payload.get('round', '?')}): {payload.get('text', '')[:300]}"
    if t == "AttemptGenerated":
        return f"\n\n*Attempt #{payload.get('iter', 0)}: {payload.get('text', '')[:200]}*"
    if t == "AttemptJudged":
        return f"\n\n*judge: {payload.get('score', 0):.2f}*"
    if t == "VoteTallied":
        return f"\n\n*🗳 winner: {payload.get('winner')} ({payload.get('share', 0):.0%})*"
    return ""
```

Replace the existing `generate_response_handler` body (preserve the current signature so Gradio bindings continue working) with:

```python
async def generate_response_handler(query, history, model, reasoning_mode,
                                    enable_critique, temperature, max_tokens,
                                    template, use_cache):
    """Drives the FastAPI backend via ReasoningAPIClient and yields
    progressive markdown for the chatbot. Replaces the legacy direct
    Reasoner.generate_response path."""
    client = _get_client()

    strategy = getattr(reasoning_mode, "value", reasoning_mode).lower()
    # Map legacy enum names to new strategy ids
    strategy = {"tree_of_thoughts": "tot", "self_consistency": "sc",
                "multi_agent_debate": "debate", "chain_of_thought": "cot",
                "analogical_reasoning": "analogical"}.get(strategy, strategy)

    try:
        run_id = await client.start_run(
            query=query, strategy=strategy, reasoning_model=model,
            temperature=temperature, max_tokens=max_tokens,
        )
    except Exception as e:
        yield f"❌ failed to start run: {e}"
        return

    accumulated = ""
    async for evt in client.stream_events(run_id):
        t = evt.get("type")
        payload = evt.get("payload", {})
        if t == "FinalAnswer":
            accumulated = payload.get("text", accumulated)
            yield accumulated
        elif t == "RunFailed":
            yield (accumulated + f"\n\n❌ run failed: {payload.get('error', 'unknown')}")
            return
        elif t == "RunCompleted":
            return
        else:
            chunk = _render_event_inline(evt)
            if chunk:
                accumulated += chunk
                yield accumulated
```

- [ ] **Step 3: Manual smoke check (no test — Gradio I/O is awkward in pytest)**

Run the FastAPI server in one terminal: `uvicorn src.api.server:app --port 8000` — wait for "Application startup complete".

In another terminal: `python -c "import asyncio; from src.ui.handlers import generate_response_handler; gen = generate_response_handler('what is 2+2', [], 'llama-3.1-8b-instant', 'simple', False, 0.7, 200, 'Custom', True); asyncio.run((lambda: [print(x) async for x in gen])())"`

Expected: prints progressively-longer strings, ending with the model's answer.

- [ ] **Step 4: Commit**

```bash
git add src/ui/handlers.py
git commit -m "refactor(ui): rewrite generate_response_handler to consume FastAPI via API client"
```

---

### Task 8.3: All-in-one launcher in main.py

**Files:**
- Modify: `main.py`

- [ ] **Step 1: Read existing main.py to see launch wiring**

Run: `cat main.py` to confirm the current launch code (theme/css passed to `demo.launch(...)` from prior fix).

- [ ] **Step 2: Add backend launcher + flag**

Replace the existing launcher block in `main.py`. The new `main.py` should:

```python
"""Entry point. Default mode: launches FastAPI backend in-process and the
Gradio UI on top of it. --no-backend skips the FastAPI process (use when
running a separate uvicorn / Next.js dev server)."""
import argparse
import asyncio
import threading
import uvicorn
from src.config.settings import AppConfig
from src.ui.app import create_ui


def _start_backend_in_thread():
    """Run uvicorn in a background daemon thread so Gradio gets the main
    thread (its launcher manages signal handling there)."""
    config = uvicorn.Config(
        "src.api.server:app",
        host=AppConfig.API_HOST, port=AppConfig.API_PORT,
        log_level="warning", access_log=False,
    )
    server = uvicorn.Server(config)
    t = threading.Thread(target=lambda: asyncio.run(server.serve()), daemon=True)
    t.start()
    return server


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-backend", action="store_true",
                        help="don't start FastAPI in-process (assume external uvicorn)")
    args = parser.parse_args()

    if not args.no_backend:
        _start_backend_in_thread()

    demo = create_ui()
    demo.launch(
        share=False,
        server_name="127.0.0.1",
        server_port=7860,
        show_error=True,
        max_threads=AppConfig.MAX_WORKERS,
        theme=getattr(demo, "_theme", None),
        css=getattr(demo, "_css", None),
    )


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Smoke run**

Run: `python main.py` — wait ~5 seconds.

In another terminal: `curl -s http://127.0.0.1:8000/health` → expect `{"status":"ok"}`.
Open `http://127.0.0.1:7860/` in a browser. Send "what is 2+2" with strategy = simple. Expect a non-empty answer.

Stop with Ctrl+C. (Daemon thread dies with main process.)

- [ ] **Step 4: Commit**

```bash
git add main.py
git commit -m "feat(launcher): all-in-one mode (FastAPI backend in background thread + Gradio UI)"
```

---

## Phase 9 — Final cleanup + smoke

### Task 9.1: Clean up legacy in-process Reasoner usage

**Files:**
- Modify: `src/ui/handlers.py` (any remaining `AdvancedReasoner` references for chat handling)
- Possibly modify: `src/ui/app.py`

- [ ] **Step 1: Find remaining direct Reasoner usage from UI**

Run: `grep -rn "AdvancedReasoner\|reasoner\.generate_response\|reasoner\.cache\|reasoner\.metrics" src/ui/`

- [ ] **Step 2: For each hit, decide:**

- If it's the chat-generation path: should already be replaced by Task 8.2.
- If it's analytics / export / cache stats: rewire to query `/runs/:id` or `/runs?conversation_id=...` via the API client. For metrics that the API doesn't yet expose, leave a `# TODO(spec-1.5)` comment and stub the UI display with `"—"`. (Do NOT silently drop the UI element.)
- If it's the legacy Reasoner instance import at module top: keep the import for now (the legacy class still exists in `src/core/reasoner.py` — Spec 1.5 deletes it).

- [ ] **Step 3: Run the full test suite**

Run: `pytest -v`
Expected: all tests pass. If any are red, fix before continuing.

- [ ] **Step 4: Smoke the end-to-end app**

Run: `python main.py`. Send one query per strategy:
- `simple`: any prompt → quick answer.
- `cot`: "what is 17 × 24" → step-by-step.
- `tot`: "plan a 3-step approach to debug a memory leak" → expect inline `💭` / `⭐` / `✂️` markers.
- `sc`: "what is 2+2 step by step" → expect `🗳` marker showing winner.
- `reflexion`: open-ended question → expect `Attempt #` markers.
- `debate`: contentious question → expect `**Analyst**` / `**Skeptic**` blocks.

Note any errors. Fix.

- [ ] **Step 5: Commit any cleanup**

```bash
git add -A
git commit -m "chore: spec 1 cleanup pass — UI surfaces for analytics + smoke fixes"
```

---

### Task 9.2: Open the PR to dev

**Files:** none

- [ ] **Step 1: Verify branch state**

Run: `git status && git log --oneline dev..HEAD`
Expected: clean working tree, full Spec 1 commit list visible.

- [ ] **Step 2: Push the branch**

Run: `git push -u origin fix/gradio-6x-compat`

If push protection blocks (likely: existing `push_error.txt` was a real secret rejection on a prior branch), inspect the offending object first:

Run: `git log -p --all -- src/api/groq_client.py | grep -i "gsk_" | head` to look for a leaked Groq key. If found, **stop and consult the user** — do not force-push or rewrite history without explicit approval.

- [ ] **Step 3: Open PR `fix/gradio-6x-compat` → `dev`**

Use `gh pr create --base dev --head fix/gradio-6x-compat` with a body that:
- Links the spec: `docs/superpowers/specs/2026-04-26-real-reasoning-algorithms-design.md`
- Lists each phase as a bullet with the headline outcome.
- Notes the unchanged HF Spaces deploy concern (open question §10 in the spec) as a follow-up before any `dev` → `main` merge.

Do **not** merge to `dev` without user approval. Do **not** touch `main`.

---

## Self-review notes

**Spec coverage:**
- §0 context / §1 architecture → Phase 0–1 set up deps + storage skeleton; Phase 7 builds the API surface; Phase 8 wires Gradio adapter (matches §1 layout).
- §2 strategy abstraction → Phase 4 (base ABC + registry stub) + Phase 5.1 (registry concretes complete it).
- §3 algorithms → Phase 5.1–5.5 (one task per algorithm + single-call wrappers).
- §4 events + SSE → Phase 2.1 (events) + 2.2 (bus) + 7.4 (SSE wire format).
- §5 SQLite schema → Phase 1.1 (DDL + pragmas) + 1.2 (DAO).
- §6 endpoints → Phase 7.1–7.4.
- §7 concurrency + errors → Phase 3.2 (semaphore in client) + 4 (TokenAccountant) + 7.3 (timeout in `start_run` background task).
- §8 Gradio→FastAPI → Phase 8.
- §9 testing → every task is TDD; Phase 3.1 builds the FakeGroqClient explicitly.

**Known gaps left as `TODO(spec-1.5)` per design:**
- Cancellation surfacing inside running strategies (DELETE sets DB status; in-flight calls finish — matches spec §7).
- Token-budget enforcement currently raises `BudgetExceeded` from `_call_reasoning`; strategies don't yet emit `TokenBudgetExceeded` and convert into a partial-result completed status. Captured in spec §7 but not split into a phase task — first run that hits the budget will surface as `RunFailed`. Acceptable for Spec 1; revisit in 1.5 if it bites.
- Gradio analytics surfaces (cache stats, model usage) need backend support that isn't in this spec. Phase 9.1 stubs them with `"—"`.

---

**Plan complete and saved to `docs/superpowers/plans/2026-04-26-real-reasoning-algorithms-plan.md`. Two execution options:**

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration.

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints.

**Which approach?**
