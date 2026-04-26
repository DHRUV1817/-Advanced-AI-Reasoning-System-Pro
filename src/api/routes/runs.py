import asyncio
import json
from typing import Optional
from fastapi import APIRouter, Request, Query
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
