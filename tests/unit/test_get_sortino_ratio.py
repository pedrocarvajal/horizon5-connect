import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "get_sortino_ratio",
    Path(__file__).parent.parent.parent / "services" / "analytic" / "helpers" / "get_sortino_ratio.py",
)
get_sortino_ratio_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(get_sortino_ratio_module)
get_sortino_ratio = get_sortino_ratio_module.get_sortino_ratio


class TestGetSortinoRatio(unittest.TestCase):
    def test_get_sortino_ratio_insufficient_data(self) -> None:
        nav_history = [1000.0]
        assert get_sortino_ratio(nav_history) == 0.0

    def test_get_sortino_ratio_empty_list(self) -> None:
        nav_history: list[float] = []
        assert get_sortino_ratio(nav_history) == 0.0

    def test_get_sortino_ratio_minimal_data(self) -> None:
        nav_history = [1000.0, 1010.0]
        result = get_sortino_ratio(nav_history)
        assert isinstance(result, float)

    def test_get_sortino_ratio_positive_returns(self) -> None:
        nav_history = [1000.0, 1010.0, 1020.0, 1030.0]
        result = get_sortino_ratio(nav_history)
        assert result >= 0

    def test_get_sortino_ratio_with_downside(self) -> None:
        nav_history = [1000.0, 990.0, 1000.0, 1010.0]
        result = get_sortino_ratio(nav_history)
        assert isinstance(result, float)

    def test_get_sortino_ratio_no_downside_returns(self) -> None:
        nav_history = [1000.0, 1010.0, 1020.0, 1030.0]
        assert get_sortino_ratio(nav_history) == 0.0

    def test_get_sortino_ratio_with_risk_free_rate(self) -> None:
        nav_history = [1000.0, 990.0, 1000.0, 1010.0]
        result_with_rf = get_sortino_ratio(nav_history, risk_free_rate=0.0001)
        result_without_rf = get_sortino_ratio(nav_history, risk_free_rate=0.0)
        assert result_with_rf < result_without_rf

    def test_get_sortino_ratio_with_zero_nav(self) -> None:
        nav_history = [1000.0, 0.0, 1000.0]
        result = get_sortino_ratio(nav_history)
        assert isinstance(result, float)

