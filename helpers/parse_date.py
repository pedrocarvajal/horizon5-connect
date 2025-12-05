"""Date parsing utilities."""

import argparse
from datetime import datetime
from typing import Any, Optional


def parse_date(
    value: str,
    date_format: str = "%Y-%m-%d",
    timezone: Any = None,
    parser: Optional[argparse.ArgumentParser] = None,
    argument: str = "--date",
) -> datetime:
    """
    Parse date string to datetime with optional timezone.

    Args:
        value: Date string to parse
        date_format: Format string (default: "%Y-%m-%d")
        timezone: Optional timezone to apply (required to avoid naive datetime)
        parser: Optional ArgumentParser to call error() on failure
        argument: Argument name for error message (default: "--date")

    Returns:
        Parsed datetime object with timezone if provided

    Raises:
        ValueError: If parsing fails and no parser provided
    """
    try:
        return datetime.strptime(value, date_format).replace(tzinfo=timezone)
    except ValueError as exception:
        error_message = f"Invalid value for {argument}. Use {date_format} format (e.g. 2024-01-31)."

        if parser is not None:
            parser.error(error_message)

        raise ValueError(error_message) from exception
