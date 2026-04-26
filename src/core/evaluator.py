"""LLM-as-judge wrappers. Every method calls the evaluator model with
JSON mode and parses the result against a Pydantic schema. Used by all
four real strategies."""
import json
from pydantic import BaseModel, Field
from typing import Any


class EvaluatorError(Exception):
    """Raised when the evaluator returns malformed JSON or violates contract."""


class ScoreResult(BaseModel):
    value: float = Field(ge=0.0, le=1.0)
    why: str = ""


class ExtractResult(BaseModel):
    answer: str
    canonical: str


class JudgeResult(BaseModel):
    score: float = Field(ge=0.0, le=1.0)
    issues: list[str] = Field(default_factory=list)


class DebateVerdict(BaseModel):
    winner: str
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str = ""
    synthesis: str


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


class Evaluator:
    def __init__(self, client, model: str):
        self.client = client
        self.model = model

    async def _json_call(self, system: str, user: str) -> dict:
        resp = await self.client.acall(
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
            model=self.model, temperature=0.0, json_mode=True,
        )
        raw = resp.choices[0].message.content
        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            raise EvaluatorError(f"evaluator returned non-JSON: {raw!r}") from e

    async def score_thought(self, *, problem: str, path: list[str]) -> ScoreResult:
        system = (
            "You score partial reasoning steps. Output strict JSON: "
            '{"value": <float 0..1>, "why": "<one sentence>"}. '
            "value=1 means clearly on track, value=0 means dead end."
        )
        user = f"Problem:\n{problem}\n\nReasoning so far:\n" + "\n→ ".join(path)
        raw = await self._json_call(system, user)
        try:
            raw["value"] = _clamp01(float(raw.get("value", 0.0)))
            return ScoreResult(**raw)
        except Exception as e:
            raise EvaluatorError(f"bad ScoreResult: {raw!r}") from e

    async def extract_answer(self, *, problem: str, sample: str) -> ExtractResult:
        system = (
            "Extract the final answer from a reasoning trace. Output JSON: "
            '{"answer": "<verbatim final answer>", "canonical": "<normalized>"}. '
            "canonical: lowercase, stripped, numbers as bare digits, no units."
        )
        user = f"Problem:\n{problem}\n\nReasoning trace:\n{sample}"
        raw = await self._json_call(system, user)
        try:
            return ExtractResult(**raw)
        except Exception as e:
            raise EvaluatorError(f"bad ExtractResult: {raw!r}") from e

    async def judge(self, *, problem: str, attempt: str) -> JudgeResult:
        system = (
            "Judge an answer's quality. Output JSON: "
            '{"score": <float 0..1>, "issues": ["<concrete issue>", ...]}. '
            "issues are specific, actionable problems the author could fix."
        )
        user = f"Problem:\n{problem}\n\nAnswer:\n{attempt}"
        raw = await self._json_call(system, user)
        try:
            raw["score"] = _clamp01(float(raw.get("score", 0.0)))
            raw.setdefault("issues", [])
            return JudgeResult(**raw)
        except Exception as e:
            raise EvaluatorError(f"bad JudgeResult: {raw!r}") from e

    async def judge_debate(self, *, problem: str,
                           transcripts: dict[str, list[str]]) -> DebateVerdict:
        system = (
            "Judge a multi-agent debate. Output JSON: "
            '{"winner": "<persona name|consensus>", "confidence": <0..1>, '
            '"rationale": "<paragraph>", "synthesis": "<final answer>"}. '
            "synthesis is what the user sees — write it well."
        )
        formatted = "\n\n".join(
            f"=== {p} ===\n" + "\n---\n".join(msgs)
            for p, msgs in transcripts.items()
        )
        user = f"Problem:\n{problem}\n\nDebate:\n{formatted}"
        raw = await self._json_call(system, user)
        try:
            raw["confidence"] = _clamp01(float(raw.get("confidence", 0.0)))
            return DebateVerdict(**raw)
        except Exception as e:
            raise EvaluatorError(f"bad DebateVerdict: {raw!r}") from e
