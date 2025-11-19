import datetime
import unittest

from helpers.get_duration import get_duration


class TestGetDuration(unittest.TestCase):
    def test_get_duration_seconds(self) -> None:
        start = datetime.datetime(2024, 1, 1, 0, 0, 0)
        end = datetime.datetime(2024, 1, 1, 0, 0, 30)
        assert get_duration(start, end) == "30 seconds"

        start = datetime.datetime(2024, 1, 1, 0, 0, 0)
        end = datetime.datetime(2024, 1, 1, 0, 0, 5)
        assert get_duration(start, end) == "5 seconds"

    def test_get_duration_minutes(self) -> None:
        start = datetime.datetime(2024, 1, 1, 0, 0, 0)
        end = datetime.datetime(2024, 1, 1, 0, 5, 0)
        assert get_duration(start, end) == "5 minutes"

        start = datetime.datetime(2024, 1, 1, 0, 0, 0)
        end = datetime.datetime(2024, 1, 1, 0, 30, 0)
        assert get_duration(start, end) == "30 minutes"

    def test_get_duration_hours(self) -> None:
        start = datetime.datetime(2024, 1, 1, 0, 0, 0)
        end = datetime.datetime(2024, 1, 1, 5, 0, 0)
        assert get_duration(start, end) == "5 hours"

        start = datetime.datetime(2024, 1, 1, 0, 0, 0)
        end = datetime.datetime(2024, 1, 1, 12, 0, 0)
        assert get_duration(start, end) == "12 hours"

    def test_get_duration_days(self) -> None:
        start = datetime.datetime(2024, 1, 1, 0, 0, 0)
        end = datetime.datetime(2024, 1, 2, 0, 0, 0)
        assert get_duration(start, end) == "1 days"

        start = datetime.datetime(2024, 1, 1, 0, 0, 0)
        end = datetime.datetime(2024, 1, 5, 0, 0, 0)
        assert get_duration(start, end) == "4 days"

    def test_get_duration_boundary_minute(self) -> None:
        start = datetime.datetime(2024, 1, 1, 0, 0, 0)
        end = datetime.datetime(2024, 1, 1, 0, 0, 59)
        assert get_duration(start, end) == "59 seconds"

        start = datetime.datetime(2024, 1, 1, 0, 0, 0)
        end = datetime.datetime(2024, 1, 1, 0, 1, 0)
        assert get_duration(start, end) == "1 minutes"

    def test_get_duration_boundary_hour(self) -> None:
        start = datetime.datetime(2024, 1, 1, 0, 0, 0)
        end = datetime.datetime(2024, 1, 1, 0, 59, 59)
        assert get_duration(start, end) == "59 minutes"

        start = datetime.datetime(2024, 1, 1, 0, 0, 0)
        end = datetime.datetime(2024, 1, 1, 1, 0, 0)
        assert get_duration(start, end) == "1 hours"

    def test_get_duration_boundary_day(self) -> None:
        start = datetime.datetime(2024, 1, 1, 0, 0, 0)
        end = datetime.datetime(2024, 1, 1, 23, 59, 59)
        assert get_duration(start, end) == "23 hours"

        start = datetime.datetime(2024, 1, 1, 0, 0, 0)
        end = datetime.datetime(2024, 1, 2, 0, 0, 0)
        assert get_duration(start, end) == "1 days"

    def test_get_duration_zero(self) -> None:
        start = datetime.datetime(2024, 1, 1, 0, 0, 0)
        end = datetime.datetime(2024, 1, 1, 0, 0, 0)
        assert get_duration(start, end) == "0 seconds"

