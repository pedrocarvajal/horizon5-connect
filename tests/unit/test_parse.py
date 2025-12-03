import unittest
from datetime import datetime

from configs.timezone import TIMEZONE
from helpers.parse import parse_float, parse_int, parse_optional_float, parse_percentage, parse_timestamp_ms


class TestParse(unittest.TestCase):
    _INT_POSITIVE: int = 42
    _INT_ZERO: int = 0
    _INT_NEGATIVE: int = -10
    _FLOAT_PI: float = 3.14
    _FLOAT_LARGE: float = 3.99
    _FLOAT_ZERO: float = 0.0
    _FLOAT_NEGATIVE: float = -10.5
    _PERCENTAGE_HALF: float = 0.5
    _PERCENTAGE_HALF_VALUE: float = 50.0
    _PERCENTAGE_FULL: float = 1.0
    _PERCENTAGE_FULL_VALUE: float = 100.0
    _PERCENTAGE_QUARTER: float = 0.25
    _PERCENTAGE_QUARTER_VALUE: float = 25.5
    _PERCENTAGE_QUARTER_RESULT: float = 0.255
    _PERCENTAGE_ALMOST_ONE: float = 0.99
    _STRING_INT_POSITIVE: str = '42'
    _STRING_INT_ZERO: str = '0'
    _STRING_INT_NEGATIVE: str = '-10'
    _STRING_FLOAT_PI: str = '3.14'
    _STRING_FLOAT_NEGATIVE: str = '-10.5'
    _STRING_PERCENTAGE_HALF: str = '0.5'
    _STRING_PERCENTAGE_HALF_VALUE: str = '50'
    _STRING_PERCENTAGE_FULL: str = '100'
    _STRING_EMPTY: str = ''
    _STRING_INVALID: str = 'invalid'

    def test_parse_int_with_integer_returns_same_value(self) -> None:
        test_cases = [
            (self._INT_POSITIVE, self._INT_POSITIVE),
            (self._INT_ZERO, self._INT_ZERO),
            (self._INT_NEGATIVE, self._INT_NEGATIVE),
        ]
        for value, expected in test_cases:
            with self.subTest(value=value):
                result = parse_int(value)
                assert result == expected

    def test_parse_int_with_string_returns_integer(self) -> None:
        test_cases = [
            (self._STRING_INT_POSITIVE, self._INT_POSITIVE),
            (self._STRING_INT_ZERO, self._INT_ZERO),
            (self._STRING_INT_NEGATIVE, self._INT_NEGATIVE),
            (self._STRING_FLOAT_PI, 3),
        ]
        for value, expected in test_cases:
            with self.subTest(value=value):
                result = parse_int(value)
                assert result == expected

    def test_parse_int_with_float_returns_truncated_integer(self) -> None:
        test_cases = [(self._FLOAT_PI, 3), (self._FLOAT_LARGE, 3)]
        for value, expected in test_cases:
            with self.subTest(value=value):
                result = parse_int(value)
                assert result == expected

    def test_parse_int_with_none_returns_zero(self) -> None:
        result = parse_int(None)
        assert result == self._INT_ZERO

    def test_parse_float_with_float_returns_same_value(self) -> None:
        test_cases = [
            (self._FLOAT_PI, self._FLOAT_PI),
            (self._FLOAT_ZERO, self._FLOAT_ZERO),
            (self._FLOAT_NEGATIVE, self._FLOAT_NEGATIVE),
        ]
        for value, expected in test_cases:
            with self.subTest(value=value):
                result = parse_float(value)
                assert result == expected

    def test_parse_float_with_string_returns_float(self) -> None:
        test_cases = [
            (self._STRING_FLOAT_PI, self._FLOAT_PI),
            (self._STRING_INT_ZERO, self._FLOAT_ZERO),
            (self._STRING_FLOAT_NEGATIVE, self._FLOAT_NEGATIVE),
        ]
        for value, expected in test_cases:
            with self.subTest(value=value):
                result = parse_float(value)
                assert result == expected

    def test_parse_float_with_integer_returns_float(self) -> None:
        test_cases = [(self._INT_POSITIVE, 42.0), (self._INT_ZERO, self._FLOAT_ZERO)]
        for value, expected in test_cases:
            with self.subTest(value=value):
                result = parse_float(value)
                assert result == expected

    def test_parse_float_with_none_returns_zero(self) -> None:
        result = parse_float(None)
        assert result == self._FLOAT_ZERO

    def test_parse_optional_float_with_float_returns_same_value(self) -> None:
        test_cases = [(self._FLOAT_PI, self._FLOAT_PI), (self._FLOAT_ZERO, self._FLOAT_ZERO)]
        for value, expected in test_cases:
            with self.subTest(value=value):
                result = parse_optional_float(value)
                assert result == expected

    def test_parse_optional_float_with_string_returns_float(self) -> None:
        test_cases = [(self._STRING_FLOAT_PI, self._FLOAT_PI), (self._STRING_INT_ZERO, self._FLOAT_ZERO)]
        for value, expected in test_cases:
            with self.subTest(value=value):
                result = parse_optional_float(value)
                assert result == expected

    def test_parse_optional_float_with_integer_returns_float(self) -> None:
        result = parse_optional_float(self._INT_POSITIVE)
        assert result == 42.0

    def test_parse_optional_float_with_none_returns_none(self) -> None:
        result = parse_optional_float(None)
        assert result is None

    def test_parse_optional_float_with_empty_string_returns_none(self) -> None:
        result = parse_optional_float(self._STRING_EMPTY)
        assert result is None

    def test_parse_optional_float_with_invalid_string_returns_none(self) -> None:
        result = parse_optional_float(self._STRING_INVALID)
        assert result is None

    def test_parse_percentage_with_float_less_than_one_returns_same_value(self) -> None:
        test_cases = [
            (self._PERCENTAGE_HALF, self._PERCENTAGE_HALF),
            (self._FLOAT_ZERO, self._FLOAT_ZERO),
            (self._PERCENTAGE_ALMOST_ONE, self._PERCENTAGE_ALMOST_ONE),
        ]
        for value, expected in test_cases:
            with self.subTest(value=value):
                result = parse_percentage(value)
                assert result == expected

    def test_parse_percentage_with_float_greater_than_one_converts_to_decimal(self) -> None:
        test_cases = [
            (self._PERCENTAGE_HALF_VALUE, self._PERCENTAGE_HALF),
            (self._PERCENTAGE_FULL_VALUE, self._PERCENTAGE_FULL),
            (self._PERCENTAGE_QUARTER_VALUE, self._PERCENTAGE_QUARTER_RESULT),
        ]
        for value, expected in test_cases:
            with self.subTest(value=value):
                result = parse_percentage(value)
                assert result == expected

    def test_parse_percentage_with_string_less_than_one_returns_decimal(self) -> None:
        result = parse_percentage(self._STRING_PERCENTAGE_HALF)
        assert result == self._PERCENTAGE_HALF

    def test_parse_percentage_with_string_greater_than_one_converts_to_decimal(self) -> None:
        test_cases = [
            (self._STRING_PERCENTAGE_HALF_VALUE, self._PERCENTAGE_HALF),
            (self._STRING_PERCENTAGE_FULL, self._PERCENTAGE_FULL),
        ]
        for value, expected in test_cases:
            with self.subTest(value=value):
                result = parse_percentage(value)
                assert result == expected

    def test_parse_percentage_with_integer_less_than_one_returns_decimal(self) -> None:
        result = parse_percentage(self._INT_ZERO)
        assert result == self._FLOAT_ZERO

    def test_parse_percentage_with_integer_greater_than_one_converts_to_decimal(self) -> None:
        test_cases = [(50, self._PERCENTAGE_HALF), (100, self._PERCENTAGE_FULL)]
        for value, expected in test_cases:
            with self.subTest(value=value):
                result = parse_percentage(value)
                assert result == expected

    def test_parse_percentage_with_none_returns_none(self) -> None:
        result = parse_percentage(None)
        assert result is None

    def test_parse_percentage_with_empty_string_returns_none(self) -> None:
        result = parse_percentage(self._STRING_EMPTY)
        assert result is None

    def test_parse_timestamp_ms_returns_positive_integer(self) -> None:
        dt = datetime(2024, 1, 1, 0, 0, 0, tzinfo=TIMEZONE)
        result = parse_timestamp_ms(dt)
        assert isinstance(result, int)
        assert result > 0

    def test_parse_timestamp_ms_epoch_returns_integer(self) -> None:
        dt = datetime(1970, 1, 1, 0, 0, 0, tzinfo=TIMEZONE)
        result = parse_timestamp_ms(dt)
        assert isinstance(result, int)
