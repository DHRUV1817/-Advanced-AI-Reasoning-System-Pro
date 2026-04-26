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
    app = build_app(api_key="test-key")

    # Manually set up app.state since lifespan won't run with ASGITransport
    app.state.db = open_db(db_path)
    run_migrations(app.state.db)
    app.state.bus = EventBus(app.state.db)
    app.state.client = AsyncGroqClient(
        api_key="test-key",
        concurrency=8,
        timeout_s=60,
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
        yield ac

    app.state.db.close()


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
