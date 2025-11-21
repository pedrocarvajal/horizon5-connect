import unittest

from services.analytic.helpers.get_cagr import get_cagr


class TestGetCagr(unittest.TestCase):
    def test_get_cagr_positive_growth(self) -> None:
        initial_nav = 1000.0
        final_nav = 1100.0
        elapsed_days = 365
        result = get_cagr(initial_nav, final_nav, elapsed_days)
        assert result > 0
        assert result < 1.0

    def test_get_cagr_negative_growth(self) -> None:
        initial_nav = 1000.0
        final_nav = 900.0
        elapsed_days = 365
        result = get_cagr(initial_nav, final_nav, elapsed_days)
        assert result < 0

    def test_get_cagr_no_growth(self) -> None:
        initial_nav = 1000.0
        final_nav = 1000.0
        elapsed_days = 365
        result = get_cagr(initial_nav, final_nav, elapsed_days)
        assert result == 0.0

    def test_get_cagr_insufficient_days(self) -> None:
        initial_nav = 1000.0
        final_nav = 1100.0
        elapsed_days = 0
        assert get_cagr(initial_nav, final_nav, elapsed_days) == 0.0

    def test_get_cagr_negative_initial_nav(self) -> None:
        initial_nav = -1000.0
        final_nav = 1100.0
        elapsed_days = 365
        assert get_cagr(initial_nav, final_nav, elapsed_days) == 0.0

    def test_get_cagr_zero_initial_nav(self) -> None:
        initial_nav = 0.0
        final_nav = 1100.0
        elapsed_days = 365
        assert get_cagr(initial_nav, final_nav, elapsed_days) == 0.0

    def test_get_cagr_total_loss(self) -> None:
        initial_nav = 1000.0
        final_nav = 0.0
        elapsed_days = 365
        assert get_cagr(initial_nav, final_nav, elapsed_days) == -1.0

    def test_get_cagr_negative_final_nav(self) -> None:
        initial_nav = 1000.0
        final_nav = -100.0
        elapsed_days = 365
        assert get_cagr(initial_nav, final_nav, elapsed_days) == -1.0

    def test_get_cagr_short_period(self) -> None:
        initial_nav = 1000.0
        final_nav = 1100.0
        elapsed_days = 30
        result = get_cagr(initial_nav, final_nav, elapsed_days)
        assert result > 0
