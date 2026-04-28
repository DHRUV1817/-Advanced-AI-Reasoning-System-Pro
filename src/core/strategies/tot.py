"""Tree of Thoughts: branch + score + prune to a beam, repeat to depth.
Reference: Yao et al., 2023.

Thought-generation calls return one thought per line (newline-separated).
"""
import asyncio
import time
import uuid
from dataclasses import dataclass, field
from src.core.events import (
    ThoughtGenerated, BranchScored, BeamPruned, BranchFailed, FinalAnswer,
    StrategyResult,
)
from src.core.strategies.base import ReasoningStrategy


@dataclass
class _Node:
    id: str
    text: str
    parent_id: str | None
    depth: int
    score: float = 0.0
    path: list[str] = field(default_factory=list)


class ToTStrategy(ReasoningStrategy):
    name = "tot"

    async def run(self, problem: str):
        t0 = time.time()
        bf = self.config.knobs.get("branching_factor", 3)
        max_depth = self.config.knobs.get("max_depth", 3)
        beam = self.config.knobs.get("beam_width", 2)
        threshold = self.config.knobs.get("score_threshold", 0.7)

        root = _Node(id="root", text="<problem>", parent_id=None,
                     depth=0, score=1.0, path=[])
        frontier = [root]

        for depth in range(1, max_depth + 1):
            children = await self._expand_frontier(problem, frontier, bf, depth)
            for c in children:
                yield ThoughtGenerated(run_id=self.run_id, payload={
                    "node_id": c.id, "parent_id": c.parent_id,
                    "depth": c.depth, "text": c.text,
                })
            if not children:
                break

            scores = await asyncio.gather(*[
                self.evaluator.score_thought(problem=problem, path=c.path)
                for c in children
            ], return_exceptions=True)
            scored: list[_Node] = []
            for c, s in zip(children, scores):
                if isinstance(s, Exception):
                    yield BranchFailed(run_id=self.run_id,
                                       payload={"node_id": c.id, "error": str(s)})
                    continue
                c.score = s.value
                scored.append(c)
                yield BranchScored(run_id=self.run_id, payload={
                    "node_id": c.id, "score": s.value, "rationale": s.why,
                })

            if not scored:
                break

            scored.sort(key=lambda n: n.score, reverse=True)
            frontier = scored[:beam]
            yield BeamPruned(run_id=self.run_id, payload={
                "depth": depth, "kept": [n.id for n in frontier],
            })

            if frontier[0].score >= threshold:
                break

        if not frontier:
            raise RuntimeError("ToT: frontier empty before synthesis")

        best = frontier[0]
        synthesis = await self._call_reasoning(messages=[
            {"role": "system", "content":
             "Synthesize a final answer using the given reasoning path."},
            {"role": "user", "content":
             f"Problem:\n{problem}\n\nBest reasoning path:\n" + "\n→ ".join(best.path)},
        ])
        yield FinalAnswer(run_id=self.run_id, payload={
            "text": synthesis, "path": best.path, "confidence": best.score,
        })
        yield StrategyResult(
            final_answer=synthesis, confidence=best.score,
            tokens_used=self.tokens.used, elapsed_s=time.time() - t0,
            trace_summary={"best_path": best.path, "best_score": best.score},
        )

    async def _expand_frontier(self, problem, frontier, bf, depth):
        async def expand(node):
            text = await self._call_reasoning(messages=[
                {"role": "system", "content":
                 f"Generate {bf} distinct next reasoning steps. "
                 "Output one per line, no numbering."},
                {"role": "user", "content":
                 f"Problem:\n{problem}\n\nReasoning so far:\n" +
                 ("\n→ ".join(node.path) if node.path else "(start)")},
            ])
            thoughts = [t.strip() for t in text.splitlines() if t.strip()][:bf]
            return node, thoughts

        results = await asyncio.gather(*[expand(n) for n in frontier],
                                       return_exceptions=True)
        out: list[_Node] = []
        for r in results:
            if isinstance(r, Exception):
                continue
            parent, thoughts = r
            for t in thoughts:
                child = _Node(id=uuid.uuid4().hex[:8], text=t,
                              parent_id=parent.id, depth=depth,
                              path=parent.path + [t])
                out.append(child)
        return out
