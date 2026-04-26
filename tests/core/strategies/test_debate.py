import pytest
from src.core.strategies.base import StrategyConfig
from src.core.strategies.debate import DebateStrategy
from src.core.evaluator import Evaluator
from src.core.events import StrategyResult
from tests.fakes.groq import FakeGroqClient


@pytest.mark.asyncio
async def test_debate_two_agents_three_rounds_then_judge():
    scripted = [
        # Round 1: 2 openings (Analyst, Skeptic)
        "Analyst opening", "Skeptic opening",
        # Round 2: 2 responses
        "Analyst r2", "Skeptic r2",
        # Round 3: 2 responses
        "Analyst r3", "Skeptic r3",
        # Judge verdict (JSON)
        {"winner": "Analyst", "confidence": 0.7,
         "rationale": "stronger arguments", "synthesis": "FINAL TEXT"},
    ]
    fake = FakeGroqClient(scripted)
    cfg = StrategyConfig(reasoning_model="rm", evaluator_model="em",
                         knobs={"n_rounds": 3,
                                "personas": ["Analyst", "Skeptic"]})
    strat = DebateStrategy(client=fake, evaluator=Evaluator(fake, model="em"),
                           config=cfg, run_id="r")
    events, result = [], None
    async for item in strat.run("q?"):
        if isinstance(item, StrategyResult):
            result = item
        else:
            events.append(item)

    spoken = [e for e in events if e.type == "AgentSpoke"]
    assert len(spoken) == 6
    assert {e.payload["agent"] for e in spoken} == {"Analyst", "Skeptic"}
    assert any(e.type == "JudgeVerdict" for e in events)
    assert result.final_answer == "FINAL TEXT"
    assert result.confidence == 0.7
