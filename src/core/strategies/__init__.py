"""Strategy registry. All 7 concrete strategies registered here."""
from src.core.strategies.base import ReasoningStrategy, StrategyConfig, BudgetExceeded
from src.core.strategies.tot import ToTStrategy
from src.core.strategies.self_consistency import SelfConsistencyStrategy
from src.core.strategies.reflexion import ReflexionStrategy
from src.core.strategies.debate import DebateStrategy
from src.core.strategies.single_call import (
    CoTStrategy, AnalogicalStrategy, SimpleStrategy,
)

STRATEGY_REGISTRY: dict[str, type[ReasoningStrategy]] = {
    "tot": ToTStrategy,
    "sc": SelfConsistencyStrategy,
    "reflexion": ReflexionStrategy,
    "debate": DebateStrategy,
    "cot": CoTStrategy,
    "analogical": AnalogicalStrategy,
    "simple": SimpleStrategy,
}

__all__ = ["STRATEGY_REGISTRY", "ReasoningStrategy", "StrategyConfig", "BudgetExceeded"]
