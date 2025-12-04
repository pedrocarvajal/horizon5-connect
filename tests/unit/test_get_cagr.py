import unittest

from services.analytic.helpers.get_cagr import get_cagr


class TestGetCagr(unittest.TestCase):
    _DEFAULT_INITIAL_NAV = 1000.0
    _GROWTH_FINAL_NAV = 1100.0
    _LOSS_FINAL_NAV = 900.0
    _DEFAULT_ELAPSED_DAYS = 365
    _SHORT_ELAPSED_DAYS = 30

    def test_get_cagr_positive_growth(self) -> None:
        result = get_cagr(
            self._DEFAULT_INITIAL_NAV,
            self._GROWTH_FINAL_NAV,
            self._DEFAULT_ELAPSED_DAYS,
        )

        assert result > 0
        assert result < 1.0
        assert abs(result - 0.1) < 0.01

    def test_get_cagr_negative_growth(self) -> None:
        result = get_cagr(
            self._DEFAULT_INITIAL_NAV,
            self._LOSS_FINAL_NAV,
            self._DEFAULT_ELAPSED_DAYS,
        )

        assert result < 0
        assert abs(result - -0.1) < 0.01

    def test_get_cagr_no_growth(self) -> None:
        result = get_cagr(
            self._DEFAULT_INITIAL_NAV,
            self._DEFAULT_INITIAL_NAV,
            self._DEFAULT_ELAPSED_DAYS,
        )

        assert result == 0.0

    def test_get_cagr_short_period(self) -> None:
        result = get_cagr(
            self._DEFAULT_INITIAL_NAV,
            self._GROWTH_FINAL_NAV,
            self._SHORT_ELAPSED_DAYS,
        )

        assert result > 0

    def test_get_cagr_insufficient_days(self) -> None:
        result = get_cagr(
            self._DEFAULT_INITIAL_NAV,
            self._GROWTH_FINAL_NAV,
            0,
        )

        assert result == 0.0

    def test_get_cagr_invalid_initial_nav(self) -> None:
        result_negative = get_cagr(
            -self._DEFAULT_INITIAL_NAV,
            self._GROWTH_FINAL_NAV,
            self._DEFAULT_ELAPSED_DAYS,
        )

        result_zero = get_cagr(
            0.0,
            self._GROWTH_FINAL_NAV,
            self._DEFAULT_ELAPSED_DAYS,
        )

        assert result_negative == 0.0
        assert result_zero == 0.0

    def test_get_cagr_invalid_final_nav(self) -> None:
        result_zero = get_cagr(
            self._DEFAULT_INITIAL_NAV,
            0.0,
            self._DEFAULT_ELAPSED_DAYS,
        )

        result_negative = get_cagr(
            self._DEFAULT_INITIAL_NAV,
            -100.0,
            self._DEFAULT_ELAPSED_DAYS,
        )

        assert result_zero == -1.0
        assert result_negative == -1.0
