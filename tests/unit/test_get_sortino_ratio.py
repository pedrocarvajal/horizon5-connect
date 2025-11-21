# Code reviewed on 2025-11-21 by Pedro Carvajal

import unittest
from typing import ClassVar

from services.analytic.helpers.get_sortino_ratio import get_sortino_ratio


class TestGetSortinoRatio(unittest.TestCase):
    # ───────────────────────────────────────────────────────────
    # CONSTANTS
    # ───────────────────────────────────────────────────────────
    _NAV_INITIAL: float = 1000.0
    _NAV_MINIMAL: ClassVar[list[float]] = [1000.0, 1010.0]
    _NAV_INCREASING: ClassVar[list[float]] = [1000.0, 1010.0, 1020.0, 1030.0]
    _NAV_WITH_DOWNSIDE: ClassVar[list[float]] = [1000.0, 990.0, 1000.0, 1010.0]
    _NAV_WITH_ZERO: ClassVar[list[float]] = [1000.0, 0.0, 1000.0]
    _RISK_FREE_RATE_WITH: float = 0.0001
    _RISK_FREE_RATE_WITHOUT: float = 0.0
    _EXPECTED_ZERO: float = 0.0

    # ───────────────────────────────────────────────────────────
    # SUCCESS CASES
    # ───────────────────────────────────────────────────────────
    def test_get_sortino_ratio_minimal_data_returns_float(self) -> None:
        """Verify Sortino ratio calculation with minimal data points."""
        result = get_sortino_ratio(self._NAV_MINIMAL)

        assert isinstance(result, float)

    def test_get_sortino_ratio_positive_returns_non_negative(self) -> None:
        """Verify Sortino ratio is non-negative with positive returns."""
        result = get_sortino_ratio(self._NAV_INCREASING)

        assert result >= 0

    def test_get_sortino_ratio_with_downside_returns_float(self) -> None:
        """Verify Sortino ratio calculation with downside returns."""
        result = get_sortino_ratio(self._NAV_WITH_DOWNSIDE)

        assert isinstance(result, float)

    def test_get_sortino_ratio_with_risk_free_rate(self) -> None:
        """Verify Sortino ratio decreases when risk-free rate is added."""
        result_with_rf = get_sortino_ratio(
            self._NAV_WITH_DOWNSIDE,
            risk_free_rate=self._RISK_FREE_RATE_WITH,
        )
        result_without_rf = get_sortino_ratio(
            self._NAV_WITH_DOWNSIDE,
            risk_free_rate=self._RISK_FREE_RATE_WITHOUT,
        )

        assert result_with_rf < result_without_rf

    # ───────────────────────────────────────────────────────────
    # EDGE CASES
    # ───────────────────────────────────────────────────────────
    def test_get_sortino_ratio_insufficient_data_returns_zero(self) -> None:
        """Verify Sortino ratio returns zero with single data point."""
        result = get_sortino_ratio([self._NAV_INITIAL])

        assert result == self._EXPECTED_ZERO

    def test_get_sortino_ratio_empty_list_returns_zero(self) -> None:
        """Verify Sortino ratio returns zero with empty list."""
        nav_history: list[float] = []
        result = get_sortino_ratio(nav_history)

        assert result == self._EXPECTED_ZERO

    def test_get_sortino_ratio_no_downside_returns_zero(self) -> None:
        """Verify Sortino ratio returns zero when no downside returns."""
        result = get_sortino_ratio(self._NAV_INCREASING)

        assert result == self._EXPECTED_ZERO

    def test_get_sortino_ratio_with_zero_nav(self) -> None:
        """Verify Sortino ratio handles zero NAV values."""
        result = get_sortino_ratio(self._NAV_WITH_ZERO)

        assert isinstance(result, float)
