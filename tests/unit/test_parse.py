import unittest
from datetime import datetime

from configs.timezone import TIMEZONE
from helpers.parse import (
    parse_float,
    parse_int,
    parse_optional_float,
    parse_percentage,
    parse_timestamp_ms,
)


class TestParse(unittest.TestCase):
    def test_parse_int_with_int(self) -> None:
        assert parse_int(42) == 42
        assert parse_int(0) == 0
        assert parse_int(-10) == -10

    def test_parse_int_with_none(self) -> None:
        assert parse_int(None) == 0

    def test_parse_int_with_string(self) -> None:
        assert parse_int("42") == 42
        assert parse_int("0") == 0
        assert parse_int("-10") == -10
        assert parse_int("3.14") == 3

    def test_parse_int_with_float(self) -> None:
        assert parse_int(3.14) == 3
        assert parse_int(3.99) == 3

    def test_parse_float_with_float(self) -> None:
        assert parse_float(3.14) == 3.14
        assert parse_float(0.0) == 0.0
        assert parse_float(-10.5) == -10.5

    def test_parse_float_with_none(self) -> None:
        assert parse_float(None) == 0.0

    def test_parse_float_with_string(self) -> None:
        assert parse_float("3.14") == 3.14
        assert parse_float("0") == 0.0
        assert parse_float("-10.5") == -10.5

    def test_parse_float_with_int(self) -> None:
        assert parse_float(42) == 42.0
        assert parse_float(0) == 0.0

    def test_parse_optional_float_with_float(self) -> None:
        assert parse_optional_float(3.14) == 3.14
        assert parse_optional_float(0.0) == 0.0

    def test_parse_optional_float_with_none(self) -> None:
        assert parse_optional_float(None) is None

    def test_parse_optional_float_with_empty_string(self) -> None:
        assert parse_optional_float("") is None

    def test_parse_optional_float_with_string(self) -> None:
        assert parse_optional_float("3.14") == 3.14
        assert parse_optional_float("0") == 0.0

    def test_parse_optional_float_with_int(self) -> None:
        assert parse_optional_float(42) == 42.0

    def test_parse_optional_float_with_invalid_string(self) -> None:
        assert parse_optional_float("invalid") is None

    def test_parse_percentage_with_float_less_than_one(self) -> None:
        assert parse_percentage(0.5) == 0.5
        assert parse_percentage(0.0) == 0.0
        assert parse_percentage(0.99) == 0.99

    def test_parse_percentage_with_float_greater_than_one(self) -> None:
        assert parse_percentage(50.0) == 0.5
        assert parse_percentage(100.0) == 1.0
        assert parse_percentage(25.5) == 0.255

    def test_parse_percentage_with_none(self) -> None:
        assert parse_percentage(None) is None

    def test_parse_percentage_with_empty_string(self) -> None:
        assert parse_percentage("") is None

    def test_parse_percentage_with_string_less_than_one(self) -> None:
        assert parse_percentage("0.5") == 0.5

    def test_parse_percentage_with_string_greater_than_one(self) -> None:
        assert parse_percentage("50") == 0.5
        assert parse_percentage("100") == 1.0

    def test_parse_percentage_with_int_less_than_one(self) -> None:
        assert parse_percentage(0) == 0.0

    def test_parse_percentage_with_int_greater_than_one(self) -> None:
        assert parse_percentage(50) == 0.5
        assert parse_percentage(100) == 1.0

    def test_parse_timestamp_ms(self) -> None:
        dt = datetime(2024, 1, 1, 0, 0, 0, tzinfo=TIMEZONE)
        timestamp_ms = parse_timestamp_ms(dt)
        assert isinstance(timestamp_ms, int)
        assert timestamp_ms > 0

        dt2 = datetime(1970, 1, 1, 0, 0, 0, tzinfo=TIMEZONE)
        timestamp_ms2 = parse_timestamp_ms(dt2)
        assert isinstance(timestamp_ms2, int)
