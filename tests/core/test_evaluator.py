import pytest
from src.core.evaluator import Evaluator, ScoreResult, ExtractResult, JudgeResult, DebateVerdict
from tests.fakes.groq import FakeGroqClient


@pytest.mark.asyncio
async def test_score_thought_parses_value_and_why():
    fake = FakeGroqClient([{"value": 0.82, "why": "logical step"}])
    ev = Evaluator(fake, model="ev-1")
    res = await ev.score_thought(problem="2+2", path=["thought"])
    assert isinstance(res, ScoreResult)
    assert res.value == 0.82
    assert res.why == "logical step"
    assert fake.calls[0]["json_mode"] is True


@pytest.mark.asyncio
async def test_score_thought_clamps_out_of_range():
    fake = FakeGroqClient([{"value": 1.5, "why": "x"}])
    ev = Evaluator(fake, model="ev-1")
    res = await ev.score_thought(problem="q", path=["t"])
    assert res.value == 1.0


@pytest.mark.asyncio
async def test_extract_answer_returns_canonical():
    fake = FakeGroqClient([{"answer": "The answer is 42.", "canonical": "42"}])
    ev = Evaluator(fake, model="ev-1")
    res = await ev.extract_answer(problem="q", sample="reasoning... 42")
    assert res.answer.endswith("42.")
    assert res.canonical == "42"


@pytest.mark.asyncio
async def test_judge_returns_score_and_issues():
    fake = FakeGroqClient([{"score": 0.6, "issues": ["unclear", "missing step"]}])
    ev = Evaluator(fake, model="ev-1")
    res = await ev.judge(problem="q", attempt="some answer")
    assert res.score == 0.6
    assert res.issues == ["unclear", "missing step"]


@pytest.mark.asyncio
async def test_judge_debate_returns_full_verdict():
    fake = FakeGroqClient([{
        "winner": "Analyst", "confidence": 0.75,
        "rationale": "stronger reasoning",
        "synthesis": "final answer text",
    }])
    ev = Evaluator(fake, model="ev-1")
    res = await ev.judge_debate(problem="q", transcripts={"Analyst": ["a"], "Skeptic": ["s"]})
    assert res.winner == "Analyst"
    assert res.confidence == 0.75
    assert res.synthesis.startswith("final")


@pytest.mark.asyncio
async def test_invalid_json_raises_evaluator_error():
    fake = FakeGroqClient(["not json at all"])
    ev = Evaluator(fake, model="ev-1")
    from src.core.evaluator import EvaluatorError
    with pytest.raises(EvaluatorError):
        await ev.score_thought(problem="q", path=["t"])
