import unittest

from services.analytic.helpers.get_calmar_ratio import get_calmar_ratio


class TestGetCalmarRatio(unittest.TestCase):
    def test_get_calmar_ratio_positive(self) -> None:
        cagr = 0.15
        max_drawdown = -0.05
        result = get_calmar_ratio(cagr, max_drawdown)
        assert abs(result - 3.0) < 0.0001

    def test_get_calmar_ratio_zero_drawdown(self) -> None:
        cagr = 0.15
        max_drawdown = 0.0
        assert get_calmar_ratio(cagr, max_drawdown) == 0.0

    def test_get_calmar_ratio_positive_drawdown(self) -> None:
        cagr = 0.15
        max_drawdown = 0.05
        assert get_calmar_ratio(cagr, max_drawdown) == 0.0

    def test_get_calmar_ratio_negative_cagr(self) -> None:
        cagr = -0.10
        max_drawdown = -0.05
        result = get_calmar_ratio(cagr, max_drawdown)
        assert abs(result - (-2.0)) < 0.0001

    def test_get_calmar_ratio_small_drawdown(self) -> None:
        cagr = 0.20
        max_drawdown = -0.01
        result = get_calmar_ratio(cagr, max_drawdown)
        assert result == 20.0

    def test_get_calmar_ratio_large_drawdown(self) -> None:
        cagr = 0.10
        max_drawdown = -0.20
        result = get_calmar_ratio(cagr, max_drawdown)
        assert result == 0.5

