import json
import pytest
from src.core.events import (
    ReasoningEvent, StrategyResult,
    RunStarted, RunCompleted, RunFailed, FinalAnswer,
    ThoughtGenerated, BranchScored, BeamPruned,
    SampleGenerated, AnswerExtracted, VoteTallied,
    AttemptGenerated, AttemptJudged, AgentSpoke, JudgeVerdict,
    new_event,
)


def test_new_event_assigns_id_and_ts():
    e = new_event(run_id="r1", type="RunStarted", payload={"strategy": "tot"})
    assert e.run_id == "r1"
    assert e.type == "RunStarted"
    assert isinstance(e.event_id, str) and len(e.event_id) >= 32
    assert e.ts > 0
    assert e.payload == {"strategy": "tot"}


def test_event_serialises_to_json_round_trip():
    e = new_event(run_id="r1", type="BranchScored",
                  payload={"node_id": "n1", "score": 0.9, "rationale": "ok"})
    blob = e.model_dump_json()
    restored = ReasoningEvent.model_validate_json(blob)
    assert restored.payload["score"] == 0.9


def test_strategy_result_required_fields():
    sr = StrategyResult(final_answer="42", confidence=0.8,
                        tokens_used=100, elapsed_s=1.0, trace_summary={})
    assert sr.confidence == 0.8


def test_concrete_event_helpers_set_type():
    assert RunStarted(run_id="r", payload={}).type == "RunStarted"
    assert FinalAnswer(run_id="r", payload={"text": "x"}).type == "FinalAnswer"
    assert BeamPruned(run_id="r", payload={"depth": 1, "kept": []}).type == "BeamPruned"
