"""Timestamp millisecond conversion utilities."""

from datetime import datetime


def parse_timestamp_ms(value: datetime) -> int:
    """
    Convert datetime to timestamp in milliseconds.

    Args:
        value: Datetime object to convert

    Returns:
        Timestamp in milliseconds
    """
    return int(value.timestamp() * 1000)
