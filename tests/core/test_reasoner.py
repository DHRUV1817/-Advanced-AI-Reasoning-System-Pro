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
    # FakeGroqClient with empty scripted list → strategy raises on first call
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
