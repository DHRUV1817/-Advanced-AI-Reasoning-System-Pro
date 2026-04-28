"""FastAPI app factory + lifespan: opens DB, runs migrations, attaches
EventBus and AsyncGroqClient to app.state. Keeps app construction
testable (no module-level side effects)."""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.storage.db import open_db, run_migrations
from src.core.event_bus import EventBus
from src.api.groq_client import AsyncGroqClient
from src.config.settings import AppConfig
from src.api.routes import meta, conversations, runs


def build_app(*, api_key: str | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.db = open_db(AppConfig.DB_PATH)
        run_migrations(app.state.db)
        app.state.bus = EventBus(app.state.db)
        # Read GROQ_API_KEY fresh from env (AppConfig was frozen at import,
        # before main.py's load_environment() ran).
        resolved_key = api_key or os.getenv("GROQ_API_KEY") or AppConfig.GROQ_API_KEY
        app.state.client = AsyncGroqClient(
            api_key=resolved_key,
            concurrency=AppConfig.LLM_CONCURRENCY,
            timeout_s=AppConfig.LLM_CALL_TIMEOUT_S,
        )
        yield
        app.state.db.close()

    app = FastAPI(title="Reasoning API", lifespan=lifespan)
    app.include_router(meta.router)
    app.include_router(conversations.router)
    app.include_router(runs.router)
    return app


app = build_app()
