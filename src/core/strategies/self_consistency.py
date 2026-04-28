"""Self-Consistency: sample N reasoning paths in parallel, extract canonical
answer from each, majority vote. Reference: Wang et al., 2022.
"""
import asyncio
import time
from collections import Counter
from src.core.events import (
    SampleGenerated, AnswerExtracted, VoteTallied, FinalAnswer,
    SampleFailed, StrategyResult,
)
from src.core.evaluator import EvaluatorError
from src.core.strategies.base import ReasoningStrategy


class SelfConsistencyStrategy(ReasoningStrategy):
    name = "sc"

    async def run(self, problem: str):
        t0 = time.time()
        n = self.config.knobs.get("n_samples", 5)
        sample_temp = self.config.knobs.get("sample_temperature", 0.9)

        # Stage 1: parallel reasoning samples
        async def one_sample():
            return await self._call_reasoning(
                messages=[
                    {"role": "system", "content":
                     "Think step by step. Show your reasoning, then state the final answer."},
                    {"role": "user", "content": problem},
                ],
                temperature=sample_temp,
            )

        samples = await asyncio.gather(
            *[one_sample() for _ in range(n)], return_exceptions=True
        )
        valid_samples: list[tuple[int, str]] = []
        for i, s in enumerate(samples):
            if isinstance(s, Exception):
                yield SampleFailed(run_id=self.run_id,
                                   payload={"sample_id": i, "error": str(s)})
                continue
            valid_samples.append((i, s))
            yield SampleGenerated(run_id=self.run_id,
                                  payload={"sample_id": i, "text": s})

        # Stage 2: parallel extraction
        async def extract(sample_text):
            return await self.evaluator.extract_answer(problem=problem, sample=sample_text)

        extracted_raw = await asyncio.gather(
            *[extract(s) for _, s in valid_samples], return_exceptions=True
        )
        extracted: list[tuple[int, str, str]] = []  # (sample_id, answer, canonical)
        for (sid, _), res in zip(valid_samples, extracted_raw):
            if isinstance(res, Exception):
                yield SampleFailed(run_id=self.run_id,
                                   payload={"sample_id": sid, "error": str(res)})
                continue
            extracted.append((sid, res.answer, res.canonical))
            yield AnswerExtracted(run_id=self.run_id, payload={
                "sample_id": sid, "answer": res.answer, "canonical": res.canonical,
            })

        if len(extracted) < 2:
            # Abort: not enough valid samples for meaningful vote
            return

        # Stage 3: vote
        tally = Counter(c for _, _, c in extracted)
        winner, count = tally.most_common(1)[0]
        share = count / n
        yield VoteTallied(run_id=self.run_id, payload={
            "tally": dict(tally), "winner": winner, "share": share,
        })

        # Pick representative full sample for the winning canonical
        representative_sid = next(sid for sid, _, c in extracted if c == winner)
        representative_text = next(s for i, s in valid_samples if i == representative_sid)

        yield FinalAnswer(run_id=self.run_id, payload={
            "text": representative_text, "vote_share": share, "confidence": share,
        })
        yield StrategyResult(
            final_answer=representative_text, confidence=share,
            tokens_used=self.tokens.used, elapsed_s=time.time() - t0,
            trace_summary={"tally": dict(tally), "winner": winner},
        )
