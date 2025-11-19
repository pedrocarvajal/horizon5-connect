import datetime
import unittest

from configs.timezone import TIMEZONE
from enums.timeframe import Timeframe
from services.strategy.helpers.get_truncated_timeframe import get_truncated_timeframe


class TestGetTruncatedTimeframe(unittest.TestCase):
    def test_get_truncated_timeframe_one_minute(self) -> None:
        date = datetime.datetime(2024, 1, 1, 12, 30, 45, 123456, tzinfo=TIMEZONE)
        result = get_truncated_timeframe(date, Timeframe.ONE_MINUTE)
        assert result.second == 0
        assert result.microsecond == 0
        assert result.minute == 30
        assert result.hour == 12

    def test_get_truncated_timeframe_one_hour(self) -> None:
        date = datetime.datetime(2024, 1, 1, 12, 30, 45, 123456, tzinfo=TIMEZONE)
        result = get_truncated_timeframe(date, Timeframe.ONE_HOUR)
        assert result.minute == 0
        assert result.second == 0
        assert result.microsecond == 0
        assert result.hour == 12

    def test_get_truncated_timeframe_one_day(self) -> None:
        date = datetime.datetime(2024, 1, 1, 12, 30, 45, 123456, tzinfo=TIMEZONE)
        result = get_truncated_timeframe(date, Timeframe.ONE_DAY)
        assert result.hour == 0
        assert result.minute == 0
        assert result.second == 0
        assert result.microsecond == 0

    def test_get_truncated_timeframe_one_week(self) -> None:
        date = datetime.datetime(2024, 1, 5, 12, 30, 45, 123456, tzinfo=TIMEZONE)
        result = get_truncated_timeframe(date, Timeframe.ONE_WEEK)
        assert result.weekday() == 0
        assert result.hour == 0
        assert result.minute == 0
        assert result.second == 0
        assert result.microsecond == 0

    def test_get_truncated_timeframe_one_month(self) -> None:
        date = datetime.datetime(2024, 1, 15, 12, 30, 45, 123456, tzinfo=TIMEZONE)
        result = get_truncated_timeframe(date, Timeframe.ONE_MONTH)
        assert result.day == 1
        assert result.hour == 0
        assert result.minute == 0
        assert result.second == 0
        assert result.microsecond == 0

    def test_get_truncated_timeframe_other_timeframe(self) -> None:
        date = datetime.datetime(2024, 1, 1, 12, 30, 45, 123456, tzinfo=TIMEZONE)
        result = get_truncated_timeframe(date, Timeframe.FIVE_MINUTES)
        assert result == date

