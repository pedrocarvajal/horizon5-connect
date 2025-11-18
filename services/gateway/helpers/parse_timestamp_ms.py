from datetime import datetime


def parse_timestamp_ms(value: datetime) -> int:
    return int(value.timestamp() * 1000)

