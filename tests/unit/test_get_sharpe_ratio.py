import unittest

from services.analytic.helpers.get_sharpe_ratio import get_sharpe_ratio


class TestGetSharpeRatio(unittest.TestCase):
    def test_get_sharpe_ratio_insufficient_data(self) -> None:
        nav_history = [1000.0]
        assert get_sharpe_ratio(nav_history) == 0.0

    def test_get_sharpe_ratio_empty_list(self) -> None:
        nav_history: list[float] = []
        assert get_sharpe_ratio(nav_history) == 0.0

    def test_get_sharpe_ratio_minimal_data(self) -> None:
        nav_history = [1000.0, 1010.0]
        result = get_sharpe_ratio(nav_history)
        assert isinstance(result, float)

    def test_get_sharpe_ratio_positive_returns(self) -> None:
        nav_history = [1000.0, 1010.0, 1020.0, 1030.0]
        result = get_sharpe_ratio(nav_history)
        assert result > 0

    def test_get_sharpe_ratio_negative_returns(self) -> None:
        nav_history = [1000.0, 990.0, 980.0, 970.0]
        result = get_sharpe_ratio(nav_history)
        assert result < 0

    def test_get_sharpe_ratio_with_risk_free_rate(self) -> None:
        nav_history = [1000.0, 1010.0, 1020.0, 1030.0]
        result_with_rf = get_sharpe_ratio(nav_history, risk_free_rate=0.0001)
        result_without_rf = get_sharpe_ratio(nav_history, risk_free_rate=0.0)
        assert result_with_rf < result_without_rf

    def test_get_sharpe_ratio_zero_volatility(self) -> None:
        nav_history = [1000.0, 1000.0, 1000.0, 1000.0]
        assert get_sharpe_ratio(nav_history) == 0.0

    def test_get_sharpe_ratio_with_zero_nav(self) -> None:
        nav_history = [1000.0, 0.0, 1000.0]
        result = get_sharpe_ratio(nav_history)
        assert isinstance(result, float)

