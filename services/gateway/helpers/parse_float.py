from typing import Any


def parse_float(value: Any) -> float:
    if value is None:
        return 0.0

    if isinstance(value, float):
        return value

    if isinstance(value, (str, int)):
        return float(value)

    return 0.0

