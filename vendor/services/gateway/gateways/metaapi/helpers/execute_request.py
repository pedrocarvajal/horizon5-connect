"""HTTP request execution helper for MetaAPI calls."""

from typing import Any, Callable, Dict, List, Optional, Union

import requests

from vendor.enums.http_status import HttpStatus


def execute_request(
    method: str,
    url: str,
    auth_token: str,
    params: Optional[Dict[str, Any]] = None,
    log_error: Optional[Callable[[str], None]] = None,
    timeout: int = 120,
) -> Optional[Union[Dict[str, Any], List[Any]]]:
    """
    Execute authenticated HTTP request to MetaAPI.

    Args:
        method: HTTP method (GET, POST, PUT, DELETE).
        url: Full request URL.
        auth_token: MetaAPI JWT authentication token.
        params: Optional query parameters.
        log_error: Optional callback function for error logging.
        timeout: Request timeout in seconds.

    Returns:
        JSON response as dict or list, or None if request fails.

    Raises:
        ValueError: If auth_token or url is missing/invalid, or method is unsupported.
    """
    if not auth_token:
        raise ValueError("auth_token is required for authenticated request")

    if not url:
        raise ValueError("URL cannot be empty")

    if method.upper() not in ["GET", "POST", "PUT", "DELETE"]:
        raise ValueError(f"Unsupported HTTP method: {method}")

    headers = {
        "Accept": "application/json",
        "auth-token": auth_token,
    }

    method_handlers = {
        "GET": requests.get,
        "POST": requests.post,
        "PUT": requests.put,
        "DELETE": requests.delete,
    }

    handler = method_handlers[method.upper()]

    try:
        response = handler(
            url,
            params=params,
            headers=headers,
            timeout=timeout,
        )

        if not HttpStatus.is_success_code(response.status_code):
            error_msg = f"HTTP Error {response.status_code}: {response.text}"

            if log_error:
                log_error(error_msg)

            return None

        return response.json()

    except requests.exceptions.RequestException as request_error:
        error_msg = f"Error making {method} request to MetaAPI: {request_error}"

        if log_error:
            log_error(error_msg)

        return None
