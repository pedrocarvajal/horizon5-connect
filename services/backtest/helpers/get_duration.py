import datetime


def get_duration(start_at: datetime.datetime, end_at: datetime.datetime) -> str:
    total_seconds = (end_at - start_at).total_seconds()
    seconds_in_minute = 60
    seconds_in_hour = 3600
    seconds_in_day = 86400

    if total_seconds < seconds_in_minute:
        seconds = int(total_seconds)
        return f"{seconds} seconds"

    if total_seconds < seconds_in_hour:
        minutes = int(total_seconds / seconds_in_minute)
        return f"{minutes} minutes"

    if total_seconds < seconds_in_day:
        hours = int(total_seconds / seconds_in_hour)
        return f"{hours} hours"

    days = int(total_seconds / seconds_in_day)
    return f"{days} days"
