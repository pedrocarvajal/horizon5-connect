# Code reviewed on 2025-11-21 by Pedro Carvajal

import unittest

from services.analytic.helpers.get_profit_factor import get_profit_factor


class TestGetProfitFactor(unittest.TestCase):
    # ───────────────────────────────────────────────────────────
    # CONSTANTS
    # ───────────────────────────────────────────────────────────
    _PROFIT_LARGE: float = 100.0
    _PROFIT_MEDIUM: float = 75.0
    _PROFIT_SMALL: float = 50.0
    _PROFIT_DOUBLE: float = 200.0
    _PROFIT_LARGE_MEDIUM: float = 150.0
    _LOSS_LARGE: float = -100.0
    _LOSS_MEDIUM: float = -75.0
    _LOSS_HALF: float = -50.0
    _LOSS_QUARTER: float = -25.0
    _EXPECTED_ZERO: float = 0.0
    _EXPECTED_HALF: float = 0.5
    _EXPECTED_ONE: float = 1.0
    _EXPECTED_TWO: float = 2.0
    _EXPECTED_TWO_QUARTER: float = 2.25
    _EXPECTED_THREE_HALF: float = 3.5

    # ───────────────────────────────────────────────────────────
    # SUCCESS CASES
    # ───────────────────────────────────────────────────────────
    def test_get_profit_factor_balanced_returns_two(self) -> None:
        """Verify profit factor with balanced wins and losses."""
        trades_profits = [
            self._PROFIT_LARGE,
            self._LOSS_HALF,
            self._PROFIT_LARGE,
            self._LOSS_HALF,
        ]
        result = get_profit_factor(trades_profits)

        assert result == self._EXPECTED_TWO

    def test_get_profit_factor_positive_returns_correct_ratio(self) -> None:
        """Verify profit factor with more wins than losses."""
        trades_profits = [
            self._PROFIT_DOUBLE,
            self._LOSS_HALF,
            self._PROFIT_LARGE_MEDIUM,
            self._LOSS_HALF,
        ]
        result = get_profit_factor(trades_profits)

        assert result == self._EXPECTED_THREE_HALF

    def test_get_profit_factor_negative_returns_less_than_one(self) -> None:
        """Verify profit factor with more losses than wins."""
        trades_profits = [
            self._PROFIT_SMALL,
            self._LOSS_LARGE,
            self._PROFIT_SMALL,
            self._LOSS_LARGE,
        ]
        result = get_profit_factor(trades_profits)

        assert result == self._EXPECTED_HALF

    def test_get_profit_factor_break_even_returns_one(self) -> None:
        """Verify profit factor returns 1.0 when wins equal losses."""
        trades_profits = [self._PROFIT_LARGE, self._LOSS_LARGE]
        result = get_profit_factor(trades_profits)

        assert result == self._EXPECTED_ONE

    def test_get_profit_factor_mixed_trades(self) -> None:
        """Verify profit factor with various trade sizes."""
        trades_profits = [
            self._PROFIT_LARGE,
            self._LOSS_QUARTER,
            self._PROFIT_SMALL,
            self._LOSS_QUARTER,
            self._PROFIT_MEDIUM,
            self._LOSS_HALF,
        ]
        result = get_profit_factor(trades_profits)

        assert result == self._EXPECTED_TWO_QUARTER

    # ───────────────────────────────────────────────────────────
    # EDGE CASES
    # ───────────────────────────────────────────────────────────
    def test_get_profit_factor_empty_list_returns_zero(self) -> None:
        """Verify profit factor returns zero with empty trades list."""
        trades_profits: list[float] = []
        result = get_profit_factor(trades_profits)

        assert result == self._EXPECTED_ZERO

    def test_get_profit_factor_only_wins_returns_zero(self) -> None:
        """Verify profit factor returns zero with only winning trades."""
        trades_profits = [self._PROFIT_LARGE, self._PROFIT_SMALL, self._PROFIT_MEDIUM]
        result = get_profit_factor(trades_profits)

        assert result == self._EXPECTED_ZERO

    def test_get_profit_factor_only_losses_returns_zero(self) -> None:
        """Verify profit factor returns zero with only losing trades."""
        trades_profits = [self._LOSS_LARGE, self._LOSS_HALF, self._LOSS_MEDIUM]
        result = get_profit_factor(trades_profits)

        assert result == self._EXPECTED_ZERO
