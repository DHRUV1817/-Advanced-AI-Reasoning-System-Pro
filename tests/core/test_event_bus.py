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
