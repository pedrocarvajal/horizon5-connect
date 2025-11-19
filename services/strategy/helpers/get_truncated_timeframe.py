# Code reviewed on 2025-11-19 by pedrocarvajal

import datetime

from enums.timeframe import Timeframe


def get_truncated_timeframe(
    date: datetime.datetime, timeframe: Timeframe
) -> datetime.datetime:
    """
    Truncate datetime to the start of the specified timeframe period.

    Args:
        date: Datetime to truncate
        timeframe: Timeframe enum (ONE_MINUTE, ONE_HOUR, ONE_DAY, ONE_WEEK, ONE_MONTH)

    Returns:
        Truncated datetime at the start of the timeframe period
        Returns original date if timeframe is not recognized
    """
    if timeframe == Timeframe.ONE_MINUTE:
        return date.replace(second=0, microsecond=0)

    if timeframe == Timeframe.ONE_HOUR:
        return date.replace(minute=0, second=0, microsecond=0)

    if timeframe == Timeframe.ONE_DAY:
        return date.replace(hour=0, minute=0, second=0, microsecond=0)

    if timeframe == Timeframe.ONE_WEEK:
        return date - datetime.timedelta(
            days=date.weekday(),
            hours=date.hour,
            minutes=date.minute,
            seconds=date.second,
            microseconds=date.microsecond,
        )

    if timeframe == Timeframe.ONE_MONTH:
        return date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    return date
