# Code reviewed on 2025-11-19 by pedrocarvajal

from time import time
from typing import Any, Callable, Dict, Optional

import requests

from enums.http_status import HttpStatus
from services.gateway.gateways.binance.helpers.generate_signature import generate_signature


def execute_request(
    method: str,
    url: str,
    api_key: str,
    api_secret: str,
    params: Optional[Dict[str, Any]] = None,
    log_error: Optional[Callable[[str], None]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Execute authenticated HTTP request to Binance API.

    Args:
        method: HTTP method (GET, POST, PUT, DELETE)
        url: Request URL
        api_key: Binance API key
        api_secret: Binance API secret
        params: Optional query parameters
        log_error: Optional callback function for error logging

    Returns:
        JSON response as dict, or None if request fails

    Raises:
        ValueError: If api_key, api_secret, or url is missing/invalid, or method is unsupported
    """
    if not api_key:
        raise ValueError("API key is required for authenticated request")

    if not api_secret:
        raise ValueError("API secret is required for authenticated request")

    if not url:
        raise ValueError("URL cannot be empty")

    if method.upper() not in ["GET", "POST", "PUT", "DELETE"]:
        raise ValueError(f"Unsupported HTTP method: {method}")

    request_params = params.copy() if params else {}
    timestamp = int(time() * 1000)
    request_params["timestamp"] = timestamp
    query_string = "&".join(f"{k}={v}" for k, v in request_params.items())
    signature = generate_signature(query_string=query_string, api_secret=api_secret)
    request_params["signature"] = signature
    headers = {"X-MBX-APIKEY": api_key}

    method_handlers = {
        "GET": requests.get,
        "POST": requests.post,
        "PUT": requests.put,
        "DELETE": requests.delete,
    }

    handler = method_handlers[method.upper()]

    try:
        response = handler(url, params=request_params, headers=headers)

        if not HttpStatus.is_success_code(response.status_code):
            error_msg = f"HTTP Error {response.status_code}: {response.text}"

            if log_error:
                log_error(error_msg)

            return None

        return response.json()

    except requests.exceptions.RequestException as e:
        error_msg = f"Error making authenticated {method} request: {e}"

        if log_error:
            log_error(error_msg)

        return None
