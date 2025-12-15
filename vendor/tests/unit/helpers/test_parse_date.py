import unittest
from datetime import datetime

from vendor.configs.timezone import TIMEZONE
from vendor.helpers.parse_date import parse_date


class TestParseDate(unittest.TestCase):
    _DEFAULT_FORMAT: str = "%Y-%m-%d"
    _CUSTOM_FORMAT: str = "%d/%m/%Y"

    def test_parse_date_with_valid_date_returns_datetime(self) -> None:
        result = parse_date("2024-01-15", timezone=TIMEZONE)

        assert isinstance(result, datetime)
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_parse_date_with_timezone_applies_timezone(self) -> None:
        result = parse_date("2024-06-20", timezone=TIMEZONE)

        assert result.tzinfo == TIMEZONE

    def test_parse_date_without_timezone_returns_none_tzinfo(self) -> None:
        result = parse_date("2024-06-20", timezone=None)

        assert result.tzinfo is None

    def test_parse_date_with_custom_format_parses_correctly(self) -> None:
        result = parse_date("15/01/2024", date_format=self._CUSTOM_FORMAT, timezone=TIMEZONE)

        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_parse_date_with_invalid_date_raises_value_error(self) -> None:
        with self.assertRaises(ValueError) as context:
            parse_date("invalid-date", timezone=TIMEZONE)

        assert "Invalid value for --date" in str(context.exception)

    def test_parse_date_with_wrong_format_raises_value_error(self) -> None:
        with self.assertRaises(ValueError) as context:
            parse_date("15/01/2024", date_format=self._DEFAULT_FORMAT, timezone=TIMEZONE)

        assert "Invalid value for --date" in str(context.exception)

    def test_parse_date_with_custom_argument_includes_in_error(self) -> None:
        with self.assertRaises(ValueError) as context:
            parse_date("invalid", argument="--start-date", timezone=TIMEZONE)

        assert "--start-date" in str(context.exception)

    def test_parse_date_boundary_values(self) -> None:
        test_cases = [
            ("2024-01-01", 2024, 1, 1),
            ("2024-12-31", 2024, 12, 31),
            ("2024-02-29", 2024, 2, 29),
        ]

        for date_str, year, month, day in test_cases:
            with self.subTest(date_str=date_str):
                result = parse_date(date_str, timezone=TIMEZONE)

                assert result.year == year
                assert result.month == month
                assert result.day == day
