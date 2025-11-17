from typing import Any, Optional


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
