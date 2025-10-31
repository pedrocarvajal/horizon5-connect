import datetime

from enums.timeframe import Timeframe


def get_truncated_timeframe(
    date: datetime.datetime, timeframe: Timeframe
) -> datetime.datetime:
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
