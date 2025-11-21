# Code reviewed on 2025-11-21 by Pedro Carvajal

import unittest
from typing import ClassVar

from services.analytic.helpers.get_r2 import get_r2


class TestGetR2(unittest.TestCase):
    # ───────────────────────────────────────────────────────────
    # CONSTANTS
    # ───────────────────────────────────────────────────────────
    _VALUE_INITIAL: float = 100.0
    _VALUES_PERFECT_LINEAR: ClassVar[list[float]] = [100.0, 110.0, 120.0, 130.0, 140.0]
    _VALUES_CONSTANT: ClassVar[list[float]] = [100.0, 100.0, 100.0, 100.0]
    _VALUES_VOLATILE: ClassVar[list[float]] = [100.0, 50.0, 150.0, 75.0, 125.0]
    _VALUES_DECLINING: ClassVar[list[float]] = [100.0, 90.0, 80.0, 70.0, 60.0]
    _VALUES_MIXED: ClassVar[list[float]] = [100.0, 105.0, 98.0, 110.0, 95.0]
    _EXPECTED_ZERO: float = 0.0
    _EXPECTED_HIGH_THRESHOLD: float = 0.9

    # ───────────────────────────────────────────────────────────
    # SUCCESS CASES
    # ───────────────────────────────────────────────────────────
    def test_get_r2_perfect_linear_returns_high_value(self) -> None:
        """Verify R2 is high with perfect linear relationship."""
        result = get_r2(self._VALUES_PERFECT_LINEAR)

        assert result > self._EXPECTED_HIGH_THRESHOLD

    def test_get_r2_volatile_returns_valid_range(self) -> None:
        """Verify R2 is within valid range with volatile values."""
        result = get_r2(self._VALUES_VOLATILE)

        assert 0.0 <= result <= 1.0

    def test_get_r2_negative_trend_returns_high_value(self) -> None:
        """Verify R2 is high with consistent negative trend."""
        result = get_r2(self._VALUES_DECLINING)

        assert result > self._EXPECTED_HIGH_THRESHOLD

    def test_get_r2_mixed_trend_returns_valid_range(self) -> None:
        """Verify R2 is within valid range with mixed trends."""
        result = get_r2(self._VALUES_MIXED)

        assert 0.0 <= result <= 1.0

    # ───────────────────────────────────────────────────────────
    # EDGE CASES
    # ───────────────────────────────────────────────────────────
    def test_get_r2_insufficient_data_returns_zero(self) -> None:
        """Verify R2 returns zero with single data point."""
        result = get_r2([self._VALUE_INITIAL])

        assert result == self._EXPECTED_ZERO

    def test_get_r2_empty_list_returns_zero(self) -> None:
        """Verify R2 returns zero with empty list."""
        values: list[float] = []
        result = get_r2(values)

        assert result == self._EXPECTED_ZERO

    def test_get_r2_no_variance_returns_zero(self) -> None:
        """Verify R2 returns zero when all values are constant."""
        result = get_r2(self._VALUES_CONSTANT)

        assert result == self._EXPECTED_ZERO
