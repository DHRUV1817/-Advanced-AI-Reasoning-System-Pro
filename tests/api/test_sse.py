import asyncio
import json
import pytest
from httpx import AsyncClient, ASGITransport
from src.api.server import build_app
from src.storage.db import open_db, run_migrations
from src.core.event_bus import EventBus
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
    if cur and "data" in cur:
        cur["data"] = json.loads(cur["data"])
        out.append(cur)
    return out


@pytest.fixture
async def client(tmp_path, monkeypatch):
    db_path = str(tmp_path / "t.db")
    monkeypatch.setattr("src.config.settings.AppConfig.DB_PATH", db_path)
    fake = FakeGroqClient(["streamed answer"])
    app = build_app(api_key="k")

    app.state.db = open_db(db_path)
    run_migrations(app.state.db)
    app.state.bus = EventBus(app.state.db)
    app.state.client = fake

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
        yield ac

    app.state.db.close()


@pytest.mark.asyncio
async def test_sse_returns_completed_run_events(client):
    cid = (await client.post("/conversations", json={})).json()["id"]
    rid = (await client.post("/runs", json={
        "conversation_id": cid, "query": "hi", "strategy": "simple",
        "reasoning_model": "m",
    })).json()["run_id"]

    # Wait until the run is done so the replay path is exercised
    for _ in range(40):
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

    for _ in range(40):
        if (await client.get(f"/runs/{rid}")).json()["status"] != "running":
            break
        await asyncio.sleep(0.05)

    r = await client.get(f"/runs/{rid}/events", headers={"Last-Event-ID": "1"})
    events = parse_sse(r.text)
    seqs = [int(e["id"]) for e in events]
    assert all(s > 1 for s in seqs)
