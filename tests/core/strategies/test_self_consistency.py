import pytest
from src.core.strategies.base import StrategyConfig
from src.core.strategies.self_consistency import SelfConsistencyStrategy
from src.core.evaluator import Evaluator
from src.core.events import StrategyResult
from tests.fakes.groq import FakeGroqClient


@pytest.mark.asyncio
async def test_sc_majority_vote_winner_and_share():
    # 5 reasoning samples, then 5 extract calls (JSON dicts)
    scripted = [
        "step a → 42", "step b → 42", "step c → 7", "step d → 42", "step e → 7",
        {"answer": "42", "canonical": "42"},
        {"answer": "42", "canonical": "42"},
        {"answer": "7",  "canonical": "7"},
        {"answer": "42", "canonical": "42"},
        {"answer": "7",  "canonical": "7"},
    ]
    fake = FakeGroqClient(scripted)
    cfg = StrategyConfig(reasoning_model="rm", evaluator_model="em",
                         knobs={"n_samples": 5})
    strat = SelfConsistencyStrategy(
        client=fake, evaluator=Evaluator(fake, model="em"),
        config=cfg, run_id="r",
    )

    events, result = [], None
    async for item in strat.run("q?"):
        if isinstance(item, StrategyResult):
            result = item
        else:
            events.append(item)

    vote = next(e for e in events if e.type == "VoteTallied")
    assert vote.payload["winner"] == "42"
    assert vote.payload["share"] == 0.6  # 3/5
    assert result.confidence == 0.6
    assert result.final_answer.endswith("42")


@pytest.mark.asyncio
async def test_sc_aborts_when_too_few_samples_survive():
    # 5 reasoning calls return text fine, but 4 of 5 extracts return invalid JSON
    scripted = [
        "x", "x", "x", "x", "x",
        {"answer": "ok", "canonical": "ok"},
        "not json", "not json", "not json", "not json",
    ]
    fake = FakeGroqClient(scripted)
    cfg = StrategyConfig(reasoning_model="rm", evaluator_model="em",
                         knobs={"n_samples": 5})
    strat = SelfConsistencyStrategy(
        client=fake, evaluator=Evaluator(fake, model="em"),
        config=cfg, run_id="r",
    )
    events = [e async for e in strat.run("q?") if not isinstance(e, StrategyResult)]
    failed = [e for e in events if e.type == "SampleFailed"]
    assert len(failed) == 4
