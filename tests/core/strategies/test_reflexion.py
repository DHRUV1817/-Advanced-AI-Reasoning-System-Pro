import pytest
from src.core.strategies.base import StrategyConfig
from src.core.strategies.reflexion import ReflexionStrategy
from src.core.evaluator import Evaluator
from src.core.events import StrategyResult
from tests.fakes.groq import FakeGroqClient


@pytest.mark.asyncio
async def test_reflexion_terminates_on_threshold():
    scripted = [
        "first attempt",
        {"score": 0.9, "issues": []},   # judge: above threshold → stop
    ]
    fake = FakeGroqClient(scripted)
    cfg = StrategyConfig(reasoning_model="rm", evaluator_model="em",
                         knobs={"max_iterations": 3, "quality_threshold": 0.85})
    strat = ReflexionStrategy(
        client=fake, evaluator=Evaluator(fake, model="em"),
        config=cfg, run_id="r",
    )
    events, result = [], None
    async for item in strat.run("q"):
        if isinstance(item, StrategyResult):
            result = item
        else:
            events.append(item)

    assert any(e.type == "TerminatedEarly" and e.payload["reason"] == "threshold" for e in events)
    assert result.final_answer == "first attempt"
    assert result.confidence == 0.9


@pytest.mark.asyncio
async def test_reflexion_iterates_when_below_threshold():
    scripted = [
        "attempt 1",
        {"score": 0.3, "issues": ["wrong"]},   # judge iter 1
        "critique 1",
        "attempt 2",
        {"score": 0.95, "issues": []},         # judge iter 2 → stop
    ]
    fake = FakeGroqClient(scripted)
    cfg = StrategyConfig(reasoning_model="rm", evaluator_model="em",
                         knobs={"max_iterations": 3, "quality_threshold": 0.9,
                                "min_improvement": 0.01})
    strat = ReflexionStrategy(
        client=fake, evaluator=Evaluator(fake, model="em"),
        config=cfg, run_id="r",
    )
    events = [e async for e in strat.run("q") if not isinstance(e, StrategyResult)]
    attempts = [e for e in events if e.type == "AttemptGenerated"]
    assert len(attempts) == 2
    assert attempts[1].payload["text"] == "attempt 2"
