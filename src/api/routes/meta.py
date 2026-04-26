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
    models = []
    # Extract all model IDs from the ModelConfig enum
    for model in ModelConfig:
        models.append(model.model_id)
    return {"models": [{"id": m} for m in models]}
