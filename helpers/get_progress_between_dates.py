# Code reviewed on 2025-11-19 by pedrocarvajal


def get_progress_between_dates(
    start_date_in_timestamp: int,
    end_date_in_timestamp: int,
    current_date_in_timestamp: int,
) -> float:
    """
    Calculate progress percentage between two timestamps.

    Args:
        start_date_in_timestamp: Start timestamp
        end_date_in_timestamp: End timestamp
        current_date_in_timestamp: Current timestamp

    Returns:
        Progress as float (0.0 = start, 1.0 = end, can be negative or > 1.0)
        Returns 1.0 if start equals end (zero duration)
    """
    traveled_time = current_date_in_timestamp - start_date_in_timestamp
    total_time = end_date_in_timestamp - start_date_in_timestamp

    if total_time == 0:
        return 1.0

    return float(traveled_time / total_time)
