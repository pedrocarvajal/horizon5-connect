# Code reviewed on 2025-11-21 by Pedro Carvajal

import unittest
from typing import ClassVar

from services.analytic.helpers.get_sharpe_ratio import get_sharpe_ratio


class TestGetSharpeRatio(unittest.TestCase):
    # ───────────────────────────────────────────────────────────
    # CONSTANTS
    # ───────────────────────────────────────────────────────────
    _NAV_INITIAL: float = 1000.0
    _NAV_MINIMAL: ClassVar[list[float]] = [1000.0, 1010.0]
    _NAV_INCREASING: ClassVar[list[float]] = [1000.0, 1010.0, 1020.0, 1030.0]
    _NAV_DECLINING: ClassVar[list[float]] = [1000.0, 990.0, 980.0, 970.0]
    _NAV_CONSTANT: ClassVar[list[float]] = [1000.0, 1000.0, 1000.0, 1000.0]
    _NAV_WITH_ZERO: ClassVar[list[float]] = [1000.0, 0.0, 1000.0]
    _RISK_FREE_RATE_WITH: float = 0.0001
    _RISK_FREE_RATE_WITHOUT: float = 0.0
    _EXPECTED_ZERO: float = 0.0

    # ───────────────────────────────────────────────────────────
    # SUCCESS CASES
    # ───────────────────────────────────────────────────────────
    def test_get_sharpe_ratio_minimal_data_returns_float(self) -> None:
        """Verify Sharpe ratio calculation with minimal data points."""
        result = get_sharpe_ratio(self._NAV_MINIMAL)

        assert isinstance(result, float)

    def test_get_sharpe_ratio_positive_returns_positive_value(self) -> None:
        """Verify Sharpe ratio is positive with positive returns."""
        result = get_sharpe_ratio(self._NAV_INCREASING)

        assert result > 0

    def test_get_sharpe_ratio_negative_returns_negative_value(self) -> None:
        """Verify Sharpe ratio is negative with negative returns."""
        result = get_sharpe_ratio(self._NAV_DECLINING)

        assert result < 0

    def test_get_sharpe_ratio_with_risk_free_rate(self) -> None:
        """Verify Sharpe ratio decreases when risk-free rate is added."""
        result_with_rf = get_sharpe_ratio(
            self._NAV_INCREASING,
            risk_free_rate=self._RISK_FREE_RATE_WITH,
        )
        result_without_rf = get_sharpe_ratio(
            self._NAV_INCREASING,
            risk_free_rate=self._RISK_FREE_RATE_WITHOUT,
        )

        assert result_with_rf < result_without_rf

    # ───────────────────────────────────────────────────────────
    # EDGE CASES
    # ───────────────────────────────────────────────────────────
    def test_get_sharpe_ratio_insufficient_data_returns_zero(self) -> None:
        """Verify Sharpe ratio returns zero with single data point."""
        result = get_sharpe_ratio([self._NAV_INITIAL])

        assert result == self._EXPECTED_ZERO

    def test_get_sharpe_ratio_empty_list_returns_zero(self) -> None:
        """Verify Sharpe ratio returns zero with empty list."""
        nav_history: list[float] = []
        result = get_sharpe_ratio(nav_history)

        assert result == self._EXPECTED_ZERO

    def test_get_sharpe_ratio_zero_volatility_returns_zero(self) -> None:
        """Verify Sharpe ratio returns zero when volatility is zero."""
        result = get_sharpe_ratio(self._NAV_CONSTANT)

        assert result == self._EXPECTED_ZERO

    def test_get_sharpe_ratio_with_zero_nav(self) -> None:
        """Verify Sharpe ratio handles zero NAV values."""
        result = get_sharpe_ratio(self._NAV_WITH_ZERO)

        assert isinstance(result, float)
