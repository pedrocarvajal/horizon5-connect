from typing import Any, Optional


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

