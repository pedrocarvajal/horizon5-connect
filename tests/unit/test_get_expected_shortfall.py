# Code reviewed on 2025-11-21 by Pedro Carvajal

import unittest
from typing import ClassVar

from services.analytic.helpers.get_expected_shortfall import get_expected_shortfall


class TestGetExpectedShortfall(unittest.TestCase):
    # ───────────────────────────────────────────────────────────
    # CONSTANTS
    # ───────────────────────────────────────────────────────────
    _NAV_INITIAL: float = 1000.0
    _NAV_DECLINING_SMALL: ClassVar[list[float]] = [1000.0, 990.0, 980.0, 970.0, 960.0]
    _NAV_DECLINING_LARGE: ClassVar[list[float]] = [1000.0, 900.0, 800.0, 700.0]
    _NAV_INCREASING: ClassVar[list[float]] = [1000.0, 1010.0, 1020.0, 1030.0]
    _NAV_WITH_ZERO: ClassVar[list[float]] = [1000.0, 0.0, 1000.0]
    _CONFIDENCE_DEFAULT: float = 0.95
    _CONFIDENCE_CUSTOM: float = 0.90
    _EXPECTED_ZERO: float = 0.0

    # ───────────────────────────────────────────────────────────
    # SUCCESS CASES
    # ───────────────────────────────────────────────────────────
    def test_get_expected_shortfall_with_default_confidence(self) -> None:
        """Verify expected shortfall calculation with default confidence level."""
        result = get_expected_shortfall(self._NAV_DECLINING_SMALL)

        assert isinstance(result, float)

    def test_get_expected_shortfall_with_custom_confidence(self) -> None:
        """Verify expected shortfall calculation with custom confidence level."""
        result = get_expected_shortfall(
            self._NAV_DECLINING_SMALL,
            confidence_level=self._CONFIDENCE_CUSTOM,
        )

        assert isinstance(result, float)

    def test_get_expected_shortfall_negative_returns(self) -> None:
        """Verify expected shortfall is negative when returns are declining."""
        result = get_expected_shortfall(self._NAV_DECLINING_LARGE)

        assert result < 0

    def test_get_expected_shortfall_positive_returns(self) -> None:
        """Verify expected shortfall calculation with positive returns."""
        result = get_expected_shortfall(self._NAV_INCREASING)

        assert isinstance(result, float)

    # ───────────────────────────────────────────────────────────
    # EDGE CASES
    # ───────────────────────────────────────────────────────────
    def test_get_expected_shortfall_insufficient_data_returns_zero(self) -> None:
        """Verify expected shortfall returns zero with single data point."""
        result = get_expected_shortfall([self._NAV_INITIAL])

        assert result == self._EXPECTED_ZERO

    def test_get_expected_shortfall_empty_list_returns_zero(self) -> None:
        """Verify expected shortfall returns zero with empty list."""
        nav_history: list[float] = []
        result = get_expected_shortfall(nav_history)

        assert result == self._EXPECTED_ZERO

    def test_get_expected_shortfall_with_zero_nav(self) -> None:
        """Verify expected shortfall handles zero NAV values."""
        result = get_expected_shortfall(self._NAV_WITH_ZERO)

        assert isinstance(result, float)
