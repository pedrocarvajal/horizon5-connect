# Code reviewed on 2025-11-19 by pedrocarvajal

from datetime import datetime
from typing import Any, Optional


def parse_int(value: Any) -> int:
    """
    Parse a value to integer, returning 0 on failure.

    Args:
        value: Value to parse (int, str, float, or None)

    Returns:
        Parsed integer value, or 0 if value is None or conversion fails
    """
    if value is None:
        return 0

    if isinstance(value, int):
        return value

    if isinstance(value, str):
        return int(float(value))

    return int(value)


def parse_float(value: Any) -> float:
    """
    Parse a value to float, returning 0.0 on failure.

    Args:
        value: Value to parse (float, int, str, or None)

    Returns:
        Parsed float value, or 0.0 if value is None or conversion fails
    """
    if value is None:
        return 0.0

    if isinstance(value, float):
        return value

    if isinstance(value, (str, int)):
        return float(value)

    return 0.0


def parse_optional_float(value: Any) -> Optional[float]:
    """
    Parse a value to float, returning None on failure.

    Args:
        value: Value to parse (float, int, str, None, or empty string)

    Returns:
        Parsed float value, or None if value is None, empty string, or conversion fails
    """
    if value is None or value == "":
        return None

    if isinstance(value, float):
        return value

    if isinstance(value, (str, int)):
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    return None


def parse_percentage(value: Any) -> Optional[float]:
    """
    Parse a percentage value, normalizing values > 1 by dividing by 100.

    Args:
        value: Percentage value (float, int, str, None, or empty string)

    Returns:
        Parsed percentage as decimal (0.0-1.0), or None if value is None or empty
        Values > 1 are divided by 100 (e.g., 50 -> 0.5, 0.5 -> 0.5)
    """
    if value is None or value == "":
        return None

    parsed_value = None

    if isinstance(value, float):
        parsed_value = value

    elif isinstance(value, (str, int)):
        parsed_value = float(value)

    if parsed_value is not None and parsed_value > 1:
        return parsed_value / 100

    return parsed_value


def parse_timestamp_ms(value: datetime) -> int:
    """
    Convert datetime to timestamp in milliseconds.

    Args:
        value: Datetime object to convert

    Returns:
        Timestamp in milliseconds
    """
    return int(value.timestamp() * 1000)
