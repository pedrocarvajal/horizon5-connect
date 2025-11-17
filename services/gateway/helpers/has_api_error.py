from typing import Any, Optional, Tuple


def has_api_error(response: Any) -> Tuple[bool, Optional[str], Optional[int]]:
    if not isinstance(response, dict):
        return False, None, None

    if "code" not in response:
        return False, None, None

    error_msg = response.get("msg", "Unknown error")
    error_code = response.get("code")

    return True, error_msg, error_code
