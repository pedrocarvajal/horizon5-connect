import unittest

from helpers.get_progress_between_dates import get_progress_between_dates


class TestGetProgressBetweenDates(unittest.TestCase):
    def test_get_progress_between_dates_start(self) -> None:
        start = 1000
        end = 2000
        current = 1000
        progress = get_progress_between_dates(start, end, current)
        assert progress == 0.0

    def test_get_progress_between_dates_middle(self) -> None:
        start = 1000
        end = 2000
        current = 1500
        progress = get_progress_between_dates(start, end, current)
        assert progress == 0.5

    def test_get_progress_between_dates_end(self) -> None:
        start = 1000
        end = 2000
        current = 2000
        progress = get_progress_between_dates(start, end, current)
        assert progress == 1.0

    def test_get_progress_between_dates_before_start(self) -> None:
        start = 1000
        end = 2000
        current = 500
        progress = get_progress_between_dates(start, end, current)
        assert progress == -0.5

    def test_get_progress_between_dates_after_end(self) -> None:
        start = 1000
        end = 2000
        current = 2500
        progress = get_progress_between_dates(start, end, current)
        assert progress == 1.5

    def test_get_progress_between_dates_zero_duration(self) -> None:
        start = 1000
        end = 1000
        current = 1000
        progress = get_progress_between_dates(start, end, current)
        assert progress == 1.0

    def test_get_progress_between_dates_quarter(self) -> None:
        start = 0
        end = 1000
        current = 250
        progress = get_progress_between_dates(start, end, current)
        assert progress == 0.25

    def test_get_progress_between_dates_three_quarters(self) -> None:
        start = 0
        end = 1000
        current = 750
        progress = get_progress_between_dates(start, end, current)
        assert progress == 0.75

    def test_get_progress_between_dates_large_numbers(self) -> None:
        start = 1000000
        end = 2000000
        current = 1500000
        progress = get_progress_between_dates(start, end, current)
        assert progress == 0.5

