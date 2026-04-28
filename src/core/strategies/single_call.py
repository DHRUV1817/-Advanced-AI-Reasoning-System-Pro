"""Wrapper strategies for the three single-call modes (CoT, Analogical, Simple).

These exist so /runs is uniform across all 7 modes and the evaluation harness
in Spec 2 can benchmark orchestrated algos against unstructured prompting
with no special-case code paths.
"""
import time
from src.core.events import FinalAnswer, StrategyResult
from src.core.strategies.base import ReasoningStrategy


_PROMPTS = {
    "cot": "You are a careful reasoner. Think step by step before answering.",
    "analogical": ("You are a reasoner who solves problems by drawing analogies "
                   "to similar problems you've seen before. Surface the analogy explicitly."),
    "simple": "Answer concisely and directly.",
}


class _SingleCallBase(ReasoningStrategy):
    async def run(self, problem: str):
        t0 = time.time()
        messages = [
            {"role": "system", "content": _PROMPTS[self.name]},
            {"role": "user", "content": problem},
        ]
        text = await self._call_reasoning(messages)
        yield FinalAnswer(run_id=self.run_id,
                          payload={"text": text, "confidence": 1.0})
        yield StrategyResult(
            final_answer=text, confidence=1.0,
            tokens_used=self.tokens.used, elapsed_s=time.time() - t0,
            trace_summary={},
        )


class CoTStrategy(_SingleCallBase):
    name = "cot"


class AnalogicalStrategy(_SingleCallBase):
    name = "analogical"


class SimpleStrategy(_SingleCallBase):
    name = "simple"
