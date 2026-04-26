import pytest
from src.core.strategies.base import (
    StrategyConfig, ReasoningStrategy, BudgetExceeded, TokenAccountant,
)
from src.core.events import StrategyResult


def test_strategy_config_defaults():
    c = StrategyConfig(reasoning_model="m1", evaluator_model="e1")
    assert c.token_budget == 50_000
    assert c.temperature == 0.7
    assert c.max_tokens == 4000
    assert c.knobs == {}


def test_token_accountant_tracks_and_raises():
    acct = TokenAccountant(budget=200)
    acct.add(80)
    acct.add(100)
    assert acct.used == 180
    with pytest.raises(BudgetExceeded):
        acct.add(50)


@pytest.mark.asyncio
async def test_strategy_subclass_must_implement_run():
    class Bad(ReasoningStrategy):
        name = "bad"
    with pytest.raises(TypeError):
        Bad(client=None, evaluator=None,
            config=StrategyConfig(reasoning_model="m", evaluator_model="e"))
