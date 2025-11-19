# Code reviewed on 2025-11-19 by pedrocarvajal

from typing import Any, Optional, Tuple


def has_api_error(response: Any) -> Tuple[bool, Optional[str], Optional[int]]:
    """
    Check if API response contains an error (Binance API format).

    Binance API returns errors in the format: {"code": <int>, "msg": "<string>"}
    This function checks if the response contains an error code.

    Args:
        response: API response (typically a dict, but can be any type)

    Returns:
        Tuple containing:
        - bool: True if error is present, False otherwise
        - Optional[str]: Error message if error present, None otherwise
        - Optional[int]: Error code if error present, None otherwise

    Examples:
        >>> has_api_error({"code": -1021, "msg": "Timestamp error"})
        (True, "Timestamp error", -1021)
        >>> has_api_error({"data": "success"})
        (False, None, None)
        >>> has_api_error(None)
        (False, None, None)
    """
    if not isinstance(response, dict):
        return False, None, None

    if "code" not in response:
        return False, None, None

    error_msg = response.get("msg", "Unknown error")
    error_code = response.get("code")

    return True, error_msg, error_code
