# Code reviewed on 2025-11-21 by Pedro Carvajal

import unittest

from services.analytic.helpers.get_calmar_ratio import get_calmar_ratio


class TestGetCalmarRatio(unittest.TestCase):
    # ───────────────────────────────────────────────────────────
    # CONSTANTS
    # ───────────────────────────────────────────────────────────
    _CAGR_POSITIVE: float = 0.15
    _CAGR_NEGATIVE: float = -0.10
    _CAGR_HIGHER: float = 0.20
    _CAGR_LOWER: float = 0.10
    _DRAWDOWN_NORMAL: float = -0.05
    _DRAWDOWN_ZERO: float = 0.0
    _DRAWDOWN_POSITIVE: float = 0.05
    _DRAWDOWN_SMALL: float = -0.01
    _DRAWDOWN_LARGE: float = -0.20
    _EXPECTED_RATIO_NORMAL: float = 3.0
    _EXPECTED_RATIO_ZERO: float = 0.0
    _EXPECTED_RATIO_NEGATIVE: float = -2.0
    _EXPECTED_RATIO_SMALL_DRAWDOWN: float = 20.0
    _EXPECTED_RATIO_LARGE_DRAWDOWN: float = 0.5
    _TOLERANCE: float = 0.0001

    # ───────────────────────────────────────────────────────────
    # SUCCESS CASES
    # ───────────────────────────────────────────────────────────
    def test_get_calmar_ratio_positive_returns_correct_value(self) -> None:
        """Verify Calmar ratio calculation with positive CAGR and negative drawdown."""
        result = get_calmar_ratio(self._CAGR_POSITIVE, self._DRAWDOWN_NORMAL)

        assert abs(result - self._EXPECTED_RATIO_NORMAL) < self._TOLERANCE

    def test_get_calmar_ratio_negative_cagr_returns_negative_ratio(self) -> None:
        """Verify Calmar ratio calculation with negative CAGR."""
        result = get_calmar_ratio(self._CAGR_NEGATIVE, self._DRAWDOWN_NORMAL)

        assert abs(result - self._EXPECTED_RATIO_NEGATIVE) < self._TOLERANCE

    def test_get_calmar_ratio_small_drawdown_returns_high_ratio(self) -> None:
        """Verify Calmar ratio with small drawdown produces high ratio."""
        result = get_calmar_ratio(self._CAGR_HIGHER, self._DRAWDOWN_SMALL)

        assert result == self._EXPECTED_RATIO_SMALL_DRAWDOWN

    def test_get_calmar_ratio_large_drawdown_returns_low_ratio(self) -> None:
        """Verify Calmar ratio with large drawdown produces low ratio."""
        result = get_calmar_ratio(self._CAGR_LOWER, self._DRAWDOWN_LARGE)

        assert result == self._EXPECTED_RATIO_LARGE_DRAWDOWN

    # ───────────────────────────────────────────────────────────
    # EDGE CASES
    # ───────────────────────────────────────────────────────────
    def test_get_calmar_ratio_zero_drawdown_returns_zero(self) -> None:
        """Verify Calmar ratio returns zero when drawdown is zero."""
        result = get_calmar_ratio(self._CAGR_POSITIVE, self._DRAWDOWN_ZERO)

        assert result == self._EXPECTED_RATIO_ZERO

    def test_get_calmar_ratio_positive_drawdown_returns_zero(self) -> None:
        """Verify Calmar ratio returns zero when drawdown is positive."""
        result = get_calmar_ratio(self._CAGR_POSITIVE, self._DRAWDOWN_POSITIVE)

        assert result == self._EXPECTED_RATIO_ZERO
