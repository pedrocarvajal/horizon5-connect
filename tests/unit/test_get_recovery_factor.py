import unittest

from services.analytic.helpers.get_recovery_factor import get_recovery_factor


class TestGetRecoveryFactor(unittest.TestCase):
    def test_get_recovery_factor_positive(self) -> None:
        net_profit_percentage = 0.10
        max_drawdown = -0.05
        result = get_recovery_factor(net_profit_percentage, max_drawdown)
        assert result == 2.0

    def test_get_recovery_factor_zero_drawdown(self) -> None:
        net_profit_percentage = 0.10
        max_drawdown = 0.0
        assert get_recovery_factor(net_profit_percentage, max_drawdown) == 0.0

    def test_get_recovery_factor_positive_drawdown(self) -> None:
        net_profit_percentage = 0.10
        max_drawdown = 0.05
        assert get_recovery_factor(net_profit_percentage, max_drawdown) == 0.0

    def test_get_recovery_factor_high_recovery(self) -> None:
        net_profit_percentage = 0.20
        max_drawdown = -0.02
        result = get_recovery_factor(net_profit_percentage, max_drawdown)
        assert result == 10.0

    def test_get_recovery_factor_low_recovery(self) -> None:
        net_profit_percentage = 0.05
        max_drawdown = -0.10
        result = get_recovery_factor(net_profit_percentage, max_drawdown)
        assert result == 0.5

    def test_get_recovery_factor_negative_profit(self) -> None:
        net_profit_percentage = -0.05
        max_drawdown = -0.10
        result = get_recovery_factor(net_profit_percentage, max_drawdown)
        assert abs(result - (-0.5)) < 0.0001

