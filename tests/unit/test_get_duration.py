# Code reviewed on 2025-11-21 by Pedro Carvajal

import datetime
import unittest

from configs.timezone import TIMEZONE
from helpers.get_duration import get_duration


class TestGetDuration(unittest.TestCase):
    # ───────────────────────────────────────────────────────────
    # CONSTANTS
    # ───────────────────────────────────────────────────────────
    _BASE_DATETIME: datetime.datetime = datetime.datetime(2024, 1, 1, 0, 0, 0, tzinfo=TIMEZONE)

    # ───────────────────────────────────────────────────────────
    # SUCCESS CASES - SECONDS
    # ───────────────────────────────────────────────────────────
    def test_get_duration_returns_seconds_format(self) -> None:
        """Verify duration formatting for values in seconds."""
        test_cases = [
            (30, "30 seconds"),
            (5, "5 seconds"),
        ]

        for seconds, expected in test_cases:
            with self.subTest(seconds=seconds):
                end = self._BASE_DATETIME + datetime.timedelta(seconds=seconds)
                result = get_duration(self._BASE_DATETIME, end)

                assert result == expected

    # ───────────────────────────────────────────────────────────
    # SUCCESS CASES - MINUTES
    # ───────────────────────────────────────────────────────────
    def test_get_duration_returns_minutes_format(self) -> None:
        """Verify duration formatting for values in minutes."""
        test_cases = [
            (5, "5 minutes"),
            (30, "30 minutes"),
        ]

        for minutes, expected in test_cases:
            with self.subTest(minutes=minutes):
                end = self._BASE_DATETIME + datetime.timedelta(minutes=minutes)
                result = get_duration(self._BASE_DATETIME, end)

                assert result == expected

    # ───────────────────────────────────────────────────────────
    # SUCCESS CASES - HOURS
    # ───────────────────────────────────────────────────────────
    def test_get_duration_returns_hours_format(self) -> None:
        """Verify duration formatting for values in hours."""
        test_cases = [
            (5, "5 hours"),
            (12, "12 hours"),
        ]

        for hours, expected in test_cases:
            with self.subTest(hours=hours):
                end = self._BASE_DATETIME + datetime.timedelta(hours=hours)
                result = get_duration(self._BASE_DATETIME, end)

                assert result == expected

    # ───────────────────────────────────────────────────────────
    # SUCCESS CASES - DAYS
    # ───────────────────────────────────────────────────────────
    def test_get_duration_returns_days_format(self) -> None:
        """Verify duration formatting for values in days."""
        test_cases = [
            (1, "1 day"),
            (4, "4 days"),
        ]

        for days, expected in test_cases:
            with self.subTest(days=days):
                end = self._BASE_DATETIME + datetime.timedelta(days=days)
                result = get_duration(self._BASE_DATETIME, end)

                assert result == expected

    # ───────────────────────────────────────────────────────────
    # BOUNDARY CASES
    # ───────────────────────────────────────────────────────────
    def test_get_duration_boundary_second_to_minute(self) -> None:
        """Verify duration formatting at second-to-minute boundary."""
        test_cases = [
            (59, "59 seconds"),
            (60, "1 minute"),
        ]

        for seconds, expected in test_cases:
            with self.subTest(seconds=seconds):
                end = self._BASE_DATETIME + datetime.timedelta(seconds=seconds)
                result = get_duration(self._BASE_DATETIME, end)

                assert result == expected

    def test_get_duration_boundary_minute_to_hour(self) -> None:
        """Verify duration formatting at minute-to-hour boundary."""
        end_59_minutes = self._BASE_DATETIME + datetime.timedelta(minutes=59, seconds=59)
        result_59_minutes = get_duration(self._BASE_DATETIME, end_59_minutes)
        assert result_59_minutes == "59 minutes"

        end_60_minutes = self._BASE_DATETIME + datetime.timedelta(hours=1)
        result_60_minutes = get_duration(self._BASE_DATETIME, end_60_minutes)
        assert result_60_minutes == "1 hour"

    def test_get_duration_boundary_hour_to_day(self) -> None:
        """Verify duration formatting at hour-to-day boundary."""
        end_23_hours = self._BASE_DATETIME + datetime.timedelta(hours=23, minutes=59, seconds=59)
        result_23_hours = get_duration(self._BASE_DATETIME, end_23_hours)
        assert result_23_hours == "23 hours"

        end_24_hours = self._BASE_DATETIME + datetime.timedelta(days=1)
        result_24_hours = get_duration(self._BASE_DATETIME, end_24_hours)
        assert result_24_hours == "1 day"

    # ───────────────────────────────────────────────────────────
    # EDGE CASES
    # ───────────────────────────────────────────────────────────
    def test_get_duration_zero_returns_zero_seconds(self) -> None:
        """Verify duration formatting when start equals end."""
        result = get_duration(self._BASE_DATETIME, self._BASE_DATETIME)

        assert result == "0 seconds"
