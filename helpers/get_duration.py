# Code reviewed on 2025-11-19 by pedrocarvajal

import datetime


def get_duration(start_at: datetime.datetime, end_at: datetime.datetime) -> str:
    """
    Calculate and format duration between two datetime objects.

    Args:
        start_at: Start datetime
        end_at: End datetime

    Returns:
        Formatted duration string (e.g., "5 seconds", "1 minute", "2 hours", "3 days")
        Returns "0 seconds" if end_at is before or equal to start_at
    """
    total_seconds = (end_at - start_at).total_seconds()
    seconds_in_minute = 60
    seconds_in_hour = 3600
    seconds_in_day = 86400

    if total_seconds <= 0:
        return "0 seconds"

    if total_seconds < seconds_in_minute:
        seconds = int(total_seconds)
        unit = "second" if seconds == 1 else "seconds"
        return f"{seconds} {unit}"

    if total_seconds < seconds_in_hour:
        minutes = int(total_seconds / seconds_in_minute)
        unit = "minute" if minutes == 1 else "minutes"
        return f"{minutes} {unit}"

    if total_seconds < seconds_in_day:
        hours = int(total_seconds / seconds_in_hour)
        unit = "hour" if hours == 1 else "hours"
        return f"{hours} {unit}"

    days = int(total_seconds / seconds_in_day)
    unit = "day" if days == 1 else "days"
    return f"{days} {unit}"
