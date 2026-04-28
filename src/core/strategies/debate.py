"""Multi-Agent Debate: distinct personas exchange responses across rounds,
judge synthesizes the final answer. Reference: Du et al., 2023.

Within-round: parallel (each agent answers independently).
Cross-round: sequential (each round needs prior responses).
"""
import asyncio
import time
from src.core.events import (
    AgentSpoke, AgentFailed, JudgeVerdict, FinalAnswer, StrategyResult,
)
from src.core.strategies.base import ReasoningStrategy


_PERSONA_PROMPTS = {
    "Analyst": ("You are the Analyst. Reason rigorously and constructively. "
                "Build the strongest case for a correct answer."),
    "Skeptic": ("You are the Skeptic. Probe assumptions and surface flaws. "
                "Challenge weak reasoning."),
}


def _persona_system(name: str) -> str:
    return _PERSONA_PROMPTS.get(name, f"You are the {name}. Argue your position carefully.")


class DebateStrategy(ReasoningStrategy):
    name = "debate"

    async def run(self, problem: str):
        t0 = time.time()
        personas: list[str] = self.config.knobs.get("personas", ["Analyst", "Skeptic"])
        n_rounds = self.config.knobs.get("n_rounds", 3)
        transcripts: dict[str, list[str]] = {p: [] for p in personas}

        # Round 1 — parallel openings
        async def open_one(persona):
            return await self._call_reasoning(messages=[
                {"role": "system", "content": _persona_system(persona)},
                {"role": "user", "content": f"Problem:\n{problem}\n\nGive your opening position."},
            ])

        opens = await asyncio.gather(*[open_one(p) for p in personas],
                                     return_exceptions=True)
        for p, msg in zip(personas, opens):
            if isinstance(msg, Exception):
                yield AgentFailed(run_id=self.run_id, payload={
                    "round": 1, "agent": p, "error": str(msg),
                })
                continue
            transcripts[p].append(msg)
            yield AgentSpoke(run_id=self.run_id, payload={
                "round": 1, "agent": p, "text": msg,
            })

        # Rounds 2..N — each agent sees other personas' last messages
        for r in range(2, n_rounds + 1):
            async def respond_one(persona):
                others_last = [transcripts[other][-1]
                               for other in personas
                               if other != persona and transcripts[other]]
                own_history = "\n---\n".join(transcripts[persona])
                others_text = "\n\n".join(others_last) or "(no rebuttal yet)"
                return await self._call_reasoning(messages=[
                    {"role": "system", "content": _persona_system(persona)},
                    {"role": "user", "content":
                     f"Problem:\n{problem}\n\nYour previous statements:\n{own_history}\n\n"
                     f"Other agents' latest:\n{others_text}\n\nRespond."},
                ])

            responses = await asyncio.gather(*[respond_one(p) for p in personas],
                                             return_exceptions=True)
            spoke_this_round = 0
            for p, msg in zip(personas, responses):
                if isinstance(msg, Exception):
                    yield AgentFailed(run_id=self.run_id, payload={
                        "round": r, "agent": p, "error": str(msg),
                    })
                    continue
                transcripts[p].append(msg)
                spoke_this_round += 1
                yield AgentSpoke(run_id=self.run_id, payload={
                    "round": r, "agent": p, "text": msg,
                })
            if spoke_this_round == 0:
                raise RuntimeError(f"debate: all agents failed in round {r}")

        # Judge
        verdict = await self.evaluator.judge_debate(problem=problem,
                                                    transcripts=transcripts)
        yield JudgeVerdict(run_id=self.run_id, payload={
            "winner": verdict.winner, "confidence": verdict.confidence,
            "rationale": verdict.rationale,
        })
        yield FinalAnswer(run_id=self.run_id, payload={
            "text": verdict.synthesis, "confidence": verdict.confidence,
            "winner": verdict.winner,
        })
        yield StrategyResult(
            final_answer=verdict.synthesis, confidence=verdict.confidence,
            tokens_used=self.tokens.used, elapsed_s=time.time() - t0,
            trace_summary={"winner": verdict.winner, "rounds": n_rounds},
        )
