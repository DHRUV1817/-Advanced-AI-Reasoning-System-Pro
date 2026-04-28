import pytest
from src.core.strategies.base import StrategyConfig
from src.core.strategies.single_call import CoTStrategy, AnalogicalStrategy, SimpleStrategy
from src.core.events import StrategyResult, FinalAnswer
from tests.fakes.groq import FakeGroqClient


@pytest.mark.parametrize("StratCls,name", [
    (CoTStrategy, "cot"), (AnalogicalStrategy, "analogical"), (SimpleStrategy, "simple"),
])
@pytest.mark.asyncio
async def test_single_call_yields_final_answer_then_result(StratCls, name):
    fake = FakeGroqClient(["the answer"])
    cfg = StrategyConfig(reasoning_model="m", evaluator_model=None)
    strat = StratCls(client=fake, evaluator=None, config=cfg, run_id="r")

    events = []
    result = None
    async for item in strat.run("q?"):
        if isinstance(item, StrategyResult):
            result = item
        else:
            events.append(item)

    assert strat.name == name
    assert any(e.type == "FinalAnswer" and e.payload["text"] == "the answer" for e in events)
    assert result is not None
    assert result.final_answer == "the answer"
    assert result.confidence == 1.0   # single-call: no scoring, full confidence
    assert result.tokens_used == 100
