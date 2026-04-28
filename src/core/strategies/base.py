"""Strategy ABC + shared config + token-budget accountant."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncGenerator, Union
from src.core.events import ReasoningEvent, StrategyResult


class BudgetExceeded(Exception):
    pass


@dataclass
class StrategyConfig:
    reasoning_model: str
    evaluator_model: str | None = None
    temperature: float = 0.7
    max_tokens: int = 4000
    token_budget: int = 50_000
    knobs: dict = field(default_factory=dict)


class TokenAccountant:
    def __init__(self, budget: int):
        self.budget = budget
        self.used = 0

    def add(self, n: int) -> None:
        if self.used + n > self.budget:
            raise BudgetExceeded(f"budget {self.budget} exceeded "
                                 f"(would reach {self.used + n})")
        self.used += n


class ReasoningStrategy(ABC):
    name: str

    def __init__(self, *, client, evaluator, config: StrategyConfig,
                 run_id: str = ""):
        self.client = client
        self.evaluator = evaluator
        self.config = config
        self.run_id = run_id
        self.tokens = TokenAccountant(config.token_budget)

    @abstractmethod
    async def run(self, problem: str) -> AsyncGenerator[
        Union[ReasoningEvent, StrategyResult], None
    ]:
        """Yield events as they happen, end with a single StrategyResult."""
        if False:
            yield  # pragma: no cover (typing hack: marks as async gen)

    async def _call_reasoning(self, messages, **kw):
        """Wrap a reasoning-model call: track tokens, propagate budget."""
        resp = await self.client.acall(
            messages=messages, model=self.config.reasoning_model,
            temperature=kw.pop("temperature", self.config.temperature),
            max_tokens=kw.pop("max_tokens", self.config.max_tokens),
            **kw,
        )
        self.tokens.add(resp.usage.total_tokens)
        return resp.choices[0].message.content
