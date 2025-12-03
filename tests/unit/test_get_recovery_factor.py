import unittest
from services.analytic.helpers.get_recovery_factor import get_recovery_factor

class TestGetRecoveryFactor(unittest.TestCase):
    _PROFIT_SMALL: float = 0.05
    _PROFIT_NORMAL: float = 0.1
    _PROFIT_LARGE: float = 0.2
    _PROFIT_NEGATIVE: float = -0.05
    _DRAWDOWN_TINY: float = -0.02
    _DRAWDOWN_SMALL: float = -0.05
    _DRAWDOWN_NORMAL: float = -0.1
    _DRAWDOWN_ZERO: float = 0.0
    _DRAWDOWN_POSITIVE: float = 0.05
    _EXPECTED_ZERO: float = 0.0
    _EXPECTED_HALF: float = 0.5
    _EXPECTED_TWO: float = 2.0
    _EXPECTED_TEN: float = 10.0
    _EXPECTED_NEGATIVE_HALF: float = -0.5
    _TOLERANCE: float = 0.0001

    def test_get_recovery_factor_positive_returns_correct_value(self) -> None:
        result = get_recovery_factor(self._PROFIT_NORMAL, self._DRAWDOWN_SMALL)
        assert result == self._EXPECTED_TWO

    def test_get_recovery_factor_high_recovery_returns_high_value(self) -> None:
        result = get_recovery_factor(self._PROFIT_LARGE, self._DRAWDOWN_TINY)
        assert result == self._EXPECTED_TEN

    def test_get_recovery_factor_low_recovery_returns_low_value(self) -> None:
        result = get_recovery_factor(self._PROFIT_SMALL, self._DRAWDOWN_NORMAL)
        assert result == self._EXPECTED_HALF

    def test_get_recovery_factor_negative_profit_returns_negative_value(self) -> None:
        result = get_recovery_factor(self._PROFIT_NEGATIVE, self._DRAWDOWN_NORMAL)
        assert abs(result - self._EXPECTED_NEGATIVE_HALF) < self._TOLERANCE

    def test_get_recovery_factor_zero_drawdown_returns_zero(self) -> None:
        result = get_recovery_factor(self._PROFIT_NORMAL, self._DRAWDOWN_ZERO)
        assert result == self._EXPECTED_ZERO

    def test_get_recovery_factor_positive_drawdown_returns_zero(self) -> None:
        result = get_recovery_factor(self._PROFIT_NORMAL, self._DRAWDOWN_POSITIVE)
        assert result == self._EXPECTED_ZERO
