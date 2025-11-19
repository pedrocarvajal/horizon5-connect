from datetime import datetime
from typing import Any, Optional


def parse_int(value: Any) -> int:
    if value is None:
        return 0

    if isinstance(value, int):
        return value

    if isinstance(value, str):
        return int(float(value))

    return int(value)


def parse_float(value: Any) -> float:
    if value is None:
        return 0.0

    if isinstance(value, float):
        return value

    if isinstance(value, (str, int)):
        return float(value)

    return 0.0


def parse_optional_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None

    if isinstance(value, float):
        return value

    if isinstance(value, (str, int)):
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    return None


def parse_percentage(value: Any) -> Optional[float]:
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


def parse_timestamp_ms(value: datetime) -> int:
    return int(value.timestamp() * 1000)
