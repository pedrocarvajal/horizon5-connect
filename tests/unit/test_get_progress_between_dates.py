import unittest

from helpers.get_progress_between_dates import get_progress_between_dates


class TestGetProgressBetweenDates(unittest.TestCase):
    _START_TIMESTAMP: int = 1000
    _END_TIMESTAMP: int = 2000
    _MIDPOINT_TIMESTAMP: int = 1500
    _QUARTER_TIMESTAMP: int = 250
    _THREE_QUARTERS_TIMESTAMP: int = 750
    _BEFORE_START_TIMESTAMP: int = 500
    _AFTER_END_TIMESTAMP: int = 2500
    _LARGE_START: int = 1000000
    _LARGE_END: int = 2000000
    _LARGE_MIDPOINT: int = 1500000
    _PROGRESS_ZERO: float = 0.0
    _PROGRESS_QUARTER: float = 0.25
    _PROGRESS_HALF: float = 0.5
    _PROGRESS_THREE_QUARTERS: float = 0.75
    _PROGRESS_COMPLETE: float = 1.0
    _PROGRESS_BEFORE_START: float = -0.5
    _PROGRESS_AFTER_END: float = 1.5

    def test_get_progress_between_dates_at_start_returns_zero(self) -> None:
        result = get_progress_between_dates(
            self._START_TIMESTAMP,
            self._END_TIMESTAMP,
            self._START_TIMESTAMP,
        )

        assert result == self._PROGRESS_ZERO

    def test_get_progress_between_dates_at_midpoint_returns_half(self) -> None:
        result = get_progress_between_dates(
            self._START_TIMESTAMP,
            self._END_TIMESTAMP,
            self._MIDPOINT_TIMESTAMP,
        )

        assert result == self._PROGRESS_HALF

    def test_get_progress_between_dates_at_end_returns_one(self) -> None:
        result = get_progress_between_dates(
            self._START_TIMESTAMP,
            self._END_TIMESTAMP,
            self._END_TIMESTAMP,
        )

        assert result == self._PROGRESS_COMPLETE

    def test_get_progress_between_dates_at_quarter_returns_quarter(self) -> None:
        result = get_progress_between_dates(
            0,
            1000,
            self._QUARTER_TIMESTAMP,
        )

        assert result == self._PROGRESS_QUARTER

    def test_get_progress_between_dates_at_three_quarters_returns_three_quarters(self) -> None:
        result = get_progress_between_dates(
            0,
            1000,
            self._THREE_QUARTERS_TIMESTAMP,
        )

        assert result == self._PROGRESS_THREE_QUARTERS

    def test_get_progress_between_dates_with_large_numbers(self) -> None:
        result = get_progress_between_dates(
            self._LARGE_START,
            self._LARGE_END,
            self._LARGE_MIDPOINT,
        )

        assert result == self._PROGRESS_HALF

    def test_get_progress_between_dates_before_start_returns_negative(self) -> None:
        result = get_progress_between_dates(
            self._START_TIMESTAMP,
            self._END_TIMESTAMP,
            self._BEFORE_START_TIMESTAMP,
        )

        assert result == self._PROGRESS_BEFORE_START

    def test_get_progress_between_dates_after_end_returns_greater_than_one(self) -> None:
        result = get_progress_between_dates(
            self._START_TIMESTAMP,
            self._END_TIMESTAMP,
            self._AFTER_END_TIMESTAMP,
        )

        assert result == self._PROGRESS_AFTER_END

    def test_get_progress_between_dates_zero_duration_returns_complete(self) -> None:
        result = get_progress_between_dates(
            self._START_TIMESTAMP,
            self._START_TIMESTAMP,
            self._START_TIMESTAMP,
        )

        assert result == self._PROGRESS_COMPLETE
