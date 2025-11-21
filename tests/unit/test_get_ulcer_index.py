# Code reviewed on 2025-11-21 by Pedro Carvajal

import unittest
from typing import ClassVar

from services.analytic.helpers.get_ulcer_index import get_ulcer_index


class TestGetUlcerIndex(unittest.TestCase):
    # ───────────────────────────────────────────────────────────
    # CONSTANTS
    # ───────────────────────────────────────────────────────────
    _NAV_INITIAL: float = 1000.0
    _NAV_INCREASING: ClassVar[list[float]] = [1000.0, 1010.0, 1020.0, 1030.0]
    _NAV_WITH_DRAWDOWN: ClassVar[list[float]] = [1000.0, 1100.0, 900.0, 1000.0]
    _NAV_LARGE_DRAWDOWN: ClassVar[list[float]] = [1000.0, 1100.0, 500.0, 600.0]
    _NAV_MULTIPLE_DRAWDOWNS: ClassVar[list[float]] = [1000.0, 1100.0, 900.0, 1050.0, 950.0, 1000.0]
    _NAV_WITH_ZERO: ClassVar[list[float]] = [1000.0, 1100.0, 0.0, 500.0]
    _EXPECTED_ZERO: float = 0.0

    # ───────────────────────────────────────────────────────────
    # SUCCESS CASES
    # ───────────────────────────────────────────────────────────
    def test_get_ulcer_index_with_drawdowns_returns_positive(self) -> None:
        """Verify Ulcer Index is positive when drawdowns exist."""
        result = get_ulcer_index(self._NAV_WITH_DRAWDOWN)

        assert result > 0

    def test_get_ulcer_index_large_drawdown_returns_positive(self) -> None:
        """Verify Ulcer Index with large drawdown returns positive value."""
        result = get_ulcer_index(self._NAV_LARGE_DRAWDOWN)

        assert result > 0

    def test_get_ulcer_index_multiple_drawdowns_returns_positive(self) -> None:
        """Verify Ulcer Index with multiple drawdowns returns positive value."""
        result = get_ulcer_index(self._NAV_MULTIPLE_DRAWDOWNS)

        assert result > 0

    # ───────────────────────────────────────────────────────────
    # EDGE CASES
    # ───────────────────────────────────────────────────────────
    def test_get_ulcer_index_insufficient_data_returns_zero(self) -> None:
        """Verify Ulcer Index returns zero with single data point."""
        result = get_ulcer_index([self._NAV_INITIAL])

        assert result == self._EXPECTED_ZERO

    def test_get_ulcer_index_empty_list_returns_zero(self) -> None:
        """Verify Ulcer Index returns zero with empty list."""
        nav_history: list[float] = []
        result = get_ulcer_index(nav_history)

        assert result == self._EXPECTED_ZERO

    def test_get_ulcer_index_no_drawdowns_returns_zero(self) -> None:
        """Verify Ulcer Index returns zero when NAV only increases."""
        result = get_ulcer_index(self._NAV_INCREASING)

        assert result == self._EXPECTED_ZERO

    def test_get_ulcer_index_with_zero_nav(self) -> None:
        """Verify Ulcer Index handles zero NAV values."""
        result = get_ulcer_index(self._NAV_WITH_ZERO)

        assert isinstance(result, float)
