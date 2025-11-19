import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "get_profit_factor",
    Path(__file__).parent.parent.parent / "services" / "analytic" / "helpers" / "get_profit_factor.py",
)
get_profit_factor_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(get_profit_factor_module)
get_profit_factor = get_profit_factor_module.get_profit_factor


class TestGetProfitFactor(unittest.TestCase):
    def test_get_profit_factor_empty_list(self) -> None:
        trades_profits: list[float] = []
        assert get_profit_factor(trades_profits) == 0.0

    def test_get_profit_factor_only_wins(self) -> None:
        trades_profits = [100.0, 50.0, 75.0]
        assert get_profit_factor(trades_profits) == 0.0

    def test_get_profit_factor_only_losses(self) -> None:
        trades_profits = [-100.0, -50.0, -75.0]
        assert get_profit_factor(trades_profits) == 0.0

    def test_get_profit_factor_balanced(self) -> None:
        trades_profits = [100.0, -50.0, 100.0, -50.0]
        result = get_profit_factor(trades_profits)
        assert result == 2.0

    def test_get_profit_factor_positive(self) -> None:
        trades_profits = [200.0, -50.0, 150.0, -50.0]
        result = get_profit_factor(trades_profits)
        assert result == 3.5

    def test_get_profit_factor_negative(self) -> None:
        trades_profits = [50.0, -100.0, 50.0, -100.0]
        result = get_profit_factor(trades_profits)
        assert result == 0.5

    def test_get_profit_factor_break_even(self) -> None:
        trades_profits = [100.0, -100.0]
        result = get_profit_factor(trades_profits)
        assert result == 1.0

    def test_get_profit_factor_mixed(self) -> None:
        trades_profits = [100.0, -25.0, 50.0, -25.0, 75.0, -50.0]
        result = get_profit_factor(trades_profits)
        assert result == 2.25

