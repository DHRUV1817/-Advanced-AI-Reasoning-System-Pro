"""Reflexion: iterative critique→refine. Reference: Shinn et al., 2023.

Sequential by design — each iteration depends on the previous attempt's
critique. Three calls per non-terminal iteration: judge, critique, refine.
"""
import time
from src.core.events import (
    AttemptGenerated, AttemptJudged, CritiqueGenerated, IterationFailed,
    TerminatedEarly, FinalAnswer, StrategyResult,
)
from src.core.strategies.base import ReasoningStrategy


class ReflexionStrategy(ReasoningStrategy):
    name = "reflexion"

    async def run(self, problem: str):
        t0 = time.time()
        max_iter = self.config.knobs.get("max_iterations", 3)
        threshold = self.config.knobs.get("quality_threshold", 0.85)
        min_improve = self.config.knobs.get("min_improvement", 0.05)

        attempt = await self._call_reasoning(messages=[
            {"role": "system", "content": "Solve the problem carefully."},
            {"role": "user", "content": problem},
        ])
        yield AttemptGenerated(run_id=self.run_id,
                               payload={"iter": 0, "text": attempt})

        prev_score = 0.0
        last_score = 0.0
        terminated_iter = 0
        for it in range(1, max_iter + 1):
            judged = await self.evaluator.judge(problem=problem, attempt=attempt)
            yield AttemptJudged(run_id=self.run_id, payload={
                "iter": it - 1, "score": judged.score, "issues": judged.issues,
            })
            last_score = judged.score
            terminated_iter = it - 1

            if judged.score >= threshold:
                yield TerminatedEarly(run_id=self.run_id, payload={
                    "reason": "threshold", "score": judged.score,
                })
                break
            if it > 1 and (judged.score - prev_score) < min_improve:
                yield TerminatedEarly(run_id=self.run_id, payload={
                    "reason": "plateau", "score": judged.score,
                })
                break

            try:
                critique = await self._call_reasoning(messages=[
                    {"role": "system", "content":
                     "You are a reviewer. Write critique addressing each issue."},
                    {"role": "user", "content":
                     f"Problem:\n{problem}\n\nAnswer:\n{attempt}\n\n"
                     f"Issues:\n- " + "\n- ".join(judged.issues)},
                ])
                yield CritiqueGenerated(run_id=self.run_id,
                                        payload={"iter": it, "text": critique})

                attempt = await self._call_reasoning(messages=[
                    {"role": "system", "content":
                     "Refine the previous answer using the critique."},
                    {"role": "user", "content":
                     f"Problem:\n{problem}\n\nPrevious answer:\n{attempt}\n\n"
                     f"Critique:\n{critique}"},
                ])
                yield AttemptGenerated(run_id=self.run_id,
                                       payload={"iter": it, "text": attempt})
            except Exception as e:
                yield IterationFailed(run_id=self.run_id,
                                      payload={"iter": it, "error": str(e)})
                break

            prev_score = judged.score

        yield FinalAnswer(run_id=self.run_id, payload={
            "text": attempt, "confidence": last_score, "iterations": terminated_iter,
        })
        yield StrategyResult(
            final_answer=attempt, confidence=last_score,
            tokens_used=self.tokens.used, elapsed_s=time.time() - t0,
            trace_summary={"final_score": last_score, "iterations": terminated_iter},
        )
