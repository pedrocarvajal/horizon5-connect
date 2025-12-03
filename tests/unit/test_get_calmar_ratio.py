import unittest
from services.analytic.helpers.get_calmar_ratio import get_calmar_ratio

class TestGetCalmarRatio(unittest.TestCase):
    _CAGR_POSITIVE: float = 0.15
    _CAGR_NEGATIVE: float = -0.1
    _CAGR_HIGHER: float = 0.2
    _CAGR_LOWER: float = 0.1
    _DRAWDOWN_NORMAL: float = -0.05
    _DRAWDOWN_ZERO: float = 0.0
    _DRAWDOWN_POSITIVE: float = 0.05
    _DRAWDOWN_SMALL: float = -0.01
    _DRAWDOWN_LARGE: float = -0.2
    _EXPECTED_RATIO_NORMAL: float = 3.0
    _EXPECTED_RATIO_ZERO: float = 0.0
    _EXPECTED_RATIO_NEGATIVE: float = -2.0
    _EXPECTED_RATIO_SMALL_DRAWDOWN: float = 20.0
    _EXPECTED_RATIO_LARGE_DRAWDOWN: float = 0.5
    _TOLERANCE: float = 0.0001

    def test_get_calmar_ratio_positive_returns_correct_value(self) -> None:
        result = get_calmar_ratio(self._CAGR_POSITIVE, self._DRAWDOWN_NORMAL)
        assert abs(result - self._EXPECTED_RATIO_NORMAL) < self._TOLERANCE

    def test_get_calmar_ratio_negative_cagr_returns_negative_ratio(self) -> None:
        result = get_calmar_ratio(self._CAGR_NEGATIVE, self._DRAWDOWN_NORMAL)
        assert abs(result - self._EXPECTED_RATIO_NEGATIVE) < self._TOLERANCE

    def test_get_calmar_ratio_small_drawdown_returns_high_ratio(self) -> None:
        result = get_calmar_ratio(self._CAGR_HIGHER, self._DRAWDOWN_SMALL)
        assert result == self._EXPECTED_RATIO_SMALL_DRAWDOWN

    def test_get_calmar_ratio_large_drawdown_returns_low_ratio(self) -> None:
        result = get_calmar_ratio(self._CAGR_LOWER, self._DRAWDOWN_LARGE)
        assert result == self._EXPECTED_RATIO_LARGE_DRAWDOWN

    def test_get_calmar_ratio_zero_drawdown_returns_zero(self) -> None:
        result = get_calmar_ratio(self._CAGR_POSITIVE, self._DRAWDOWN_ZERO)
        assert result == self._EXPECTED_RATIO_ZERO

    def test_get_calmar_ratio_positive_drawdown_returns_zero(self) -> None:
        result = get_calmar_ratio(self._CAGR_POSITIVE, self._DRAWDOWN_POSITIVE)
        assert result == self._EXPECTED_RATIO_ZERO
