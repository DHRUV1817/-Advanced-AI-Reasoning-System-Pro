import pytest
from src.core.strategies.base import StrategyConfig
from src.core.strategies.tot import ToTStrategy
from src.core.evaluator import Evaluator
from src.core.events import StrategyResult
from tests.fakes.groq import FakeGroqClient


def _scripted_tree(branching, beam, depth):
    """Build a deterministic script: each thought-gen call returns N
    newline-joined thoughts; each evaluator call returns a known score."""
    out = []
    # depth 1: 1 root call → branching thoughts; then `branching` eval calls
    out.append("\n".join(f"thought-d1-{i}" for i in range(branching)))
    out += [{"value": 0.9 - 0.1 * i, "why": ""} for i in range(branching)]
    # depth 2..depth: beam expansions
    for d in range(2, depth + 1):
        for b in range(beam):
            out.append("\n".join(f"thought-d{d}-b{b}-{i}" for i in range(branching)))
        out += [{"value": 0.9 - 0.05 * i, "why": ""} for i in range(beam * branching)]
    # synthesis
    out.append("FINAL")
    return out


@pytest.mark.asyncio
async def test_tot_runs_to_synthesis():
    fake = FakeGroqClient(_scripted_tree(branching=3, beam=2, depth=2))
    cfg = StrategyConfig(reasoning_model="rm", evaluator_model="em",
                         knobs={"branching_factor": 3, "beam_width": 2,
                                "max_depth": 2, "score_threshold": 0.99})
    strat = ToTStrategy(client=fake, evaluator=Evaluator(fake, model="em"),
                        config=cfg, run_id="r")
    events, result = [], None
    async for item in strat.run("solve x"):
        if isinstance(item, StrategyResult):
            result = item
        else:
            events.append(item)

    assert any(e.type == "BeamPruned" for e in events)
    pruned = [e for e in events if e.type == "BeamPruned"]
    assert all(len(e.payload["kept"]) <= 2 for e in pruned)
    assert any(e.type == "FinalAnswer" and e.payload["text"] == "FINAL" for e in events)
    assert result.final_answer == "FINAL"
    assert 0.0 <= result.confidence <= 1.0


@pytest.mark.asyncio
async def test_tot_early_stops_on_threshold():
    # depth 1 produces a 0.95 score → above threshold of 0.9
    scripted = [
        "t1\nt2\nt3",
        {"value": 0.95, "why": ""}, {"value": 0.4, "why": ""}, {"value": 0.4, "why": ""},
        "EARLY-FINAL",   # synthesis
    ]
    fake = FakeGroqClient(scripted)
    cfg = StrategyConfig(reasoning_model="rm", evaluator_model="em",
                         knobs={"branching_factor": 3, "beam_width": 2,
                                "max_depth": 5, "score_threshold": 0.9})
    strat = ToTStrategy(client=fake, evaluator=Evaluator(fake, model="em"),
                        config=cfg, run_id="r")
    events = [e async for e in strat.run("q") if not isinstance(e, StrategyResult)]
    pruned = [e for e in events if e.type == "BeamPruned"]
    assert len(pruned) == 1   # stopped after depth 1
