import asyncio
import pytest
from httpx import AsyncClient, ASGITransport
from src.api.server import build_app
from src.storage.db import open_db, run_migrations
from src.core.event_bus import EventBus
from tests.fakes.groq import FakeGroqClient


@pytest.fixture
async def client(tmp_path, monkeypatch):
    db_path = str(tmp_path / "t.db")
    monkeypatch.setattr("src.config.settings.AppConfig.DB_PATH", db_path)
    fake = FakeGroqClient(["hello world"])
    app = build_app(api_key="k")

    # Manual app.state init (ASGITransport doesn't run lifespan).
    # CRITICAL: assign the FakeGroqClient (not real one) so tests don't hit the network.
    app.state.db = open_db(db_path)
    run_migrations(app.state.db)
    app.state.bus = EventBus(app.state.db)
    app.state.client = fake

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
        yield ac, fake

    app.state.db.close()


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
    for _ in range(40):
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
