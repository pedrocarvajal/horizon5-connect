"""Percentage parsing utilities."""

from typing import Any, Optional


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
