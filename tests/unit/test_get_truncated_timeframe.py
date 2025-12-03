import datetime
import unittest

from configs.timezone import TIMEZONE
from enums.timeframe import Timeframe
from services.strategy.helpers.get_truncated_timeframe import get_truncated_timeframe


class TestGetTruncatedTimeframe(unittest.TestCase):
    _DATETIME_FULL: datetime.datetime = datetime.datetime(2024, 1, 1, 12, 30, 45, 123456, tzinfo=TIMEZONE)
    _DATETIME_WEEK_MID: datetime.datetime = datetime.datetime(2024, 1, 5, 12, 30, 45, 123456, tzinfo=TIMEZONE)
    _DATETIME_MONTH_MID: datetime.datetime = datetime.datetime(2024, 1, 15, 12, 30, 45, 123456, tzinfo=TIMEZONE)
    _EXPECTED_ZERO: int = 0
    _EXPECTED_HOUR: int = 12
    _EXPECTED_MINUTE: int = 30
    _EXPECTED_DAY: int = 1
    _EXPECTED_WEEKDAY_MONDAY: int = 0

    def test_get_truncated_timeframe_one_minute_truncates_seconds(self) -> None:
        result = get_truncated_timeframe(self._DATETIME_FULL, Timeframe.ONE_MINUTE)
        assert result.second == self._EXPECTED_ZERO
        assert result.microsecond == self._EXPECTED_ZERO
        assert result.minute == self._EXPECTED_MINUTE
        assert result.hour == self._EXPECTED_HOUR

    def test_get_truncated_timeframe_one_hour_truncates_minutes(self) -> None:
        result = get_truncated_timeframe(self._DATETIME_FULL, Timeframe.ONE_HOUR)
        assert result.minute == self._EXPECTED_ZERO
        assert result.second == self._EXPECTED_ZERO
        assert result.microsecond == self._EXPECTED_ZERO
        assert result.hour == self._EXPECTED_HOUR

    def test_get_truncated_timeframe_one_day_truncates_hours(self) -> None:
        result = get_truncated_timeframe(self._DATETIME_FULL, Timeframe.ONE_DAY)
        assert result.hour == self._EXPECTED_ZERO
        assert result.minute == self._EXPECTED_ZERO
        assert result.second == self._EXPECTED_ZERO
        assert result.microsecond == self._EXPECTED_ZERO

    def test_get_truncated_timeframe_one_week_truncates_to_monday(self) -> None:
        result = get_truncated_timeframe(self._DATETIME_WEEK_MID, Timeframe.ONE_WEEK)
        assert result.weekday() == self._EXPECTED_WEEKDAY_MONDAY
        assert result.hour == self._EXPECTED_ZERO
        assert result.minute == self._EXPECTED_ZERO
        assert result.second == self._EXPECTED_ZERO
        assert result.microsecond == self._EXPECTED_ZERO

    def test_get_truncated_timeframe_one_month_truncates_to_first_day(self) -> None:
        result = get_truncated_timeframe(self._DATETIME_MONTH_MID, Timeframe.ONE_MONTH)
        assert result.day == self._EXPECTED_DAY
        assert result.hour == self._EXPECTED_ZERO
        assert result.minute == self._EXPECTED_ZERO
        assert result.second == self._EXPECTED_ZERO
        assert result.microsecond == self._EXPECTED_ZERO

    def test_get_truncated_timeframe_other_timeframe_returns_original(self) -> None:
        result = get_truncated_timeframe(self._DATETIME_FULL, Timeframe.FIVE_MINUTES)
        assert result == self._DATETIME_FULL
