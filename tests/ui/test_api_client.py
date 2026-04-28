import asyncio
import pytest
from httpx import AsyncClient, ASGITransport
from src.api.server import build_app
from src.storage.db import open_db, run_migrations
from src.core.event_bus import EventBus
from src.ui.api_client import ReasoningAPIClient
from tests.fakes.groq import FakeGroqClient


@pytest.fixture
async def app_and_client(tmp_path, monkeypatch):
    db_path = str(tmp_path / "t.db")
    monkeypatch.setattr("src.config.settings.AppConfig.DB_PATH", db_path)
    fake = FakeGroqClient(["hi", "hi"])
    app = build_app(api_key="k")

    # Manual app.state init (ASGITransport doesn't run lifespan)
    app.state.db = open_db(db_path)
    run_migrations(app.state.db)
    app.state.bus = EventBus(app.state.db)
    app.state.client = fake

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
        client = ReasoningAPIClient(base_url="http://test", http_client=http)
        yield client

    app.state.db.close()


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
