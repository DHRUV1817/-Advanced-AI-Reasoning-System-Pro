"""Pydantic models for streamed reasoning events + final result.

Every concrete event is a thin subclass that hardcodes `type`. This keeps
the wire format flat (one JSON envelope per event) while letting strategies
construct events with `XYZ(run_id=..., payload=...)` instead of fiddly
type strings.
"""
import time
import uuid
from typing import Any
from pydantic import BaseModel, Field


def _new_event_id() -> str:
    return uuid.uuid4().hex


class ReasoningEvent(BaseModel):
    event_id: str = Field(default_factory=_new_event_id)
    run_id: str
    type: str
    ts: float = Field(default_factory=time.time)
    payload: dict[str, Any] = Field(default_factory=dict)


class StrategyResult(BaseModel):
    final_answer: str
    confidence: float
    tokens_used: int
    elapsed_s: float
    trace_summary: dict[str, Any] = Field(default_factory=dict)


def new_event(*, run_id: str, type: str, payload: dict) -> ReasoningEvent:
    return ReasoningEvent(run_id=run_id, type=type, payload=payload)


def _typed(name: str):
    """Factory that builds a thin subclass with a frozen `type` field."""
    class _T(ReasoningEvent):
        type: str = name
    _T.__name__ = name
    return _T


# Lifecycle
RunStarted = _typed("RunStarted")
RunCompleted = _typed("RunCompleted")
RunFailed = _typed("RunFailed")
TokenBudgetExceeded = _typed("TokenBudgetExceeded")
FinalAnswer = _typed("FinalAnswer")

# ToT
ThoughtGenerated = _typed("ThoughtGenerated")
BranchScored = _typed("BranchScored")
BeamPruned = _typed("BeamPruned")
BranchFailed = _typed("BranchFailed")

# Self-Consistency
SampleGenerated = _typed("SampleGenerated")
AnswerExtracted = _typed("AnswerExtracted")
VoteTallied = _typed("VoteTallied")
SampleFailed = _typed("SampleFailed")

# Reflexion
AttemptGenerated = _typed("AttemptGenerated")
AttemptJudged = _typed("AttemptJudged")
CritiqueGenerated = _typed("CritiqueGenerated")
IterationFailed = _typed("IterationFailed")
TerminatedEarly = _typed("TerminatedEarly")

# Debate
AgentSpoke = _typed("AgentSpoke")
AgentFailed = _typed("AgentFailed")
JudgeVerdict = _typed("JudgeVerdict")
