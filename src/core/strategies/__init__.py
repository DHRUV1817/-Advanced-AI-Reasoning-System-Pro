"""Strategy registry. Concrete strategies register themselves on import."""
from src.core.strategies.base import ReasoningStrategy, StrategyConfig, BudgetExceeded

# Concrete strategies are lazily imported in Phase 5
# For now, initialize an empty registry that gets populated when concrete strategies are available
STRATEGY_REGISTRY: dict[str, type[ReasoningStrategy]] = {}

def _init_registry():
    """Populate registry with concrete strategies (called when all are available)."""
    global STRATEGY_REGISTRY
    try:
        from src.core.strategies.tot import ToTStrategy
        from src.core.strategies.self_consistency import SelfConsistencyStrategy
        from src.core.strategies.reflexion import ReflexionStrategy
        from src.core.strategies.debate import DebateStrategy
        from src.core.strategies.single_call import (
            CoTStrategy, AnalogicalStrategy, SimpleStrategy,
        )

        STRATEGY_REGISTRY = {
            "tot": ToTStrategy,
            "sc": SelfConsistencyStrategy,
            "reflexion": ReflexionStrategy,
            "debate": DebateStrategy,
            "cot": CoTStrategy,
            "analogical": AnalogicalStrategy,
            "simple": SimpleStrategy,
        }
    except ImportError:
        # Concrete strategies not yet implemented; that's okay in Phase 4
        pass

# Try to initialize, but don't fail if concrete strategies aren't available yet
_init_registry()

__all__ = ["STRATEGY_REGISTRY", "ReasoningStrategy", "StrategyConfig", "BudgetExceeded"]
