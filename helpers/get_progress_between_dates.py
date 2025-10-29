def get_progress_between_dates(
    start_date_in_timestamp: int,
    end_date_in_timestamp: int,
    current_date_in_timestamp: int,
) -> float:
    traveled_time = current_date_in_timestamp - start_date_in_timestamp
    total_time = end_date_in_timestamp - start_date_in_timestamp

    if total_time == 0:
        return 1

    return float(traveled_time / total_time)
