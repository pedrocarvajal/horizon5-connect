"""Optional float parsing utilities."""

from typing import Any, Optional


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
