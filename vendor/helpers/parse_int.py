"""Integer parsing utilities."""

from typing import Any


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
