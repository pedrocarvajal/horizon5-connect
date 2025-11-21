import unittest

from services.analytic.helpers.get_ulcer_index import get_ulcer_index


class TestGetUlcerIndex(unittest.TestCase):
    def test_get_ulcer_index_insufficient_data(self) -> None:
        nav_history = [1000.0]
        assert get_ulcer_index(nav_history) == 0.0

    def test_get_ulcer_index_empty_list(self) -> None:
        nav_history: list[float] = []
        assert get_ulcer_index(nav_history) == 0.0

    def test_get_ulcer_index_no_drawdowns(self) -> None:
        nav_history = [1000.0, 1010.0, 1020.0, 1030.0]
        assert get_ulcer_index(nav_history) == 0.0

    def test_get_ulcer_index_with_drawdowns(self) -> None:
        nav_history = [1000.0, 1100.0, 900.0, 1000.0]
        result = get_ulcer_index(nav_history)
        assert result > 0

    def test_get_ulcer_index_large_drawdown(self) -> None:
        nav_history = [1000.0, 1100.0, 500.0, 600.0]
        result = get_ulcer_index(nav_history)
        assert result > 0

    def test_get_ulcer_index_multiple_drawdowns(self) -> None:
        nav_history = [1000.0, 1100.0, 900.0, 1050.0, 950.0, 1000.0]
        result = get_ulcer_index(nav_history)
        assert result > 0

    def test_get_ulcer_index_with_zero_nav(self) -> None:
        nav_history = [1000.0, 1100.0, 0.0, 500.0]
        result = get_ulcer_index(nav_history)
        assert isinstance(result, float)

