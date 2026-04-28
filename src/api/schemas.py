"""Pydantic request/response models for the FastAPI surface."""
from typing import Optional, Any
from pydantic import BaseModel, Field


class StartRunRequest(BaseModel):
    conversation_id: Optional[str] = None
    query: str
    strategy: str
    reasoning_model: str
    evaluator_model: Optional[str] = None
    knobs: dict[str, Any] = Field(default_factory=dict)
    token_budget: Optional[int] = None
    temperature: float = 0.7
    max_tokens: int = 4000


class StartRunResponse(BaseModel):
    run_id: str
    status: str = "running"


class RunRow(BaseModel):
    id: str
    conversation_id: str
    created_at: float
    completed_at: Optional[float]
    status: str
    strategy: str
    reasoning_model: str
    evaluator_model: Optional[str]
    query: str
    knobs: dict
    final_answer: Optional[str]
    confidence: Optional[float]
    tokens_used: int
    elapsed_s: Optional[float]
    error: Optional[str]


class CreateConversationRequest(BaseModel):
    title: Optional[str] = None


class ErrorResponse(BaseModel):
    error: str
    code: str
