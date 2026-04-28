import pytest
from httpx import AsyncClient, ASGITransport
from src.api.server import build_app
from src.storage.db import open_db, run_migrations
from src.core.event_bus import EventBus
from src.api.groq_client import AsyncGroqClient


@pytest.fixture
async def client(tmp_path, monkeypatch):
    db_path = str(tmp_path / "t.db")
    monkeypatch.setattr("src.config.settings.AppConfig.DB_PATH", db_path)
    app = build_app(api_key="k")

    # Manual app.state init (ASGITransport doesn't run lifespan)
    app.state.db = open_db(db_path)
    run_migrations(app.state.db)
    app.state.bus = EventBus(app.state.db)
    app.state.client = AsyncGroqClient(api_key="k", concurrency=8, timeout_s=60)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
        yield ac

    app.state.db.close()


@pytest.mark.asyncio
async def test_create_and_list_conversation(client):
    r = await client.post("/conversations", json={"title": "first"})
    assert r.status_code == 200
    cid = r.json()["id"]

    r2 = await client.get("/conversations")
    assert any(c["id"] == cid and c["title"] == "first" for c in r2.json()["conversations"])
