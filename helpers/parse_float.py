"""Float parsing utilities."""

from typing import Any


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
