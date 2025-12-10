"""Base provider for HTTP API integrations."""

import json
from abc import ABC
from typing import Any, Dict, Optional

import requests

from providers.exceptions import ProviderHTTPError, ProviderRequestError
from services.logging import LoggingService


class BaseProvider(ABC):
    """Abstract base class for HTTP API providers.

    Provides common HTTP methods (GET, POST, PUT, PATCH, DELETE) with error
    handling, logging, and configurable headers and timeout.

    Attributes:
        _base_url: Base URL for API requests.
        _headers: Default headers for all requests.
        _timeout: Request timeout in seconds.
        _logger: Logging service instance.
    """

    _base_url: str
    _headers: Dict[str, str]
    _timeout: int

    _logger: LoggingService

    def __init__(
        self,
        base_url: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 30,
    ) -> None:
        """Initialize the provider with base URL, headers, and timeout.

        Args:
            base_url: Base URL for API requests.
            headers: Optional default headers for all requests.
            timeout: Request timeout in seconds.
        """
        self._base_url = base_url.rstrip("/")
        self._headers = headers or {}
        self._timeout = timeout

        self._logger = LoggingService()

        self._validate_configuration()

    def delete(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Send DELETE request to the specified endpoint.

        Args:
            endpoint: API endpoint path.
            data: Optional request body data.
            headers: Optional additional headers.

        Returns:
            JSON response as dictionary.
        """
        return self._request(
            "DELETE",
            endpoint,
            data=data,
            headers=headers,
        )

    def get(
        self,
        endpoint: str,
        query: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Send GET request to the specified endpoint.

        Args:
            endpoint: API endpoint path.
            query: Optional query parameters.
            headers: Optional additional headers.

        Returns:
            JSON response as dictionary.
        """
        return self._request(
            "GET",
            endpoint,
            query=query,
            headers=headers,
        )

    def patch(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Send PATCH request to the specified endpoint.

        Args:
            endpoint: API endpoint path.
            data: Optional request body data.
            headers: Optional additional headers.

        Returns:
            JSON response as dictionary.
        """
        return self._request(
            "PATCH",
            endpoint,
            data=data,
            headers=headers,
        )

    def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Send POST request to the specified endpoint.

        Args:
            endpoint: API endpoint path.
            data: Optional request body data.
            headers: Optional additional headers.

        Returns:
            JSON response as dictionary.
        """
        return self._request(
            "POST",
            endpoint,
            data=data,
            headers=headers,
        )

    def put(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Send PUT request to the specified endpoint.

        Args:
            endpoint: API endpoint path.
            data: Optional request body data.
            headers: Optional additional headers.

        Returns:
            JSON response as dictionary.
        """
        return self._request(
            "PUT",
            endpoint,
            data=data,
            headers=headers,
        )

    def _build_url(self, endpoint: str) -> str:
        endpoint = endpoint.lstrip("/")
        return f"{self._base_url}/{endpoint}"

    def _log_response_error(self, response_body: str) -> None:
        try:
            data = json.loads(response_body)
            message = data.get("message")
            error_message = data.get("error", {}).get("message") if isinstance(data.get("error"), dict) else None

            if message:
                self._logger.error(f"Response message: {message}")
            if error_message:
                self._logger.error(f"Error details: {error_message}")

        except Exception as e:
            self._logger.error(str(e))

    def _request(
        self,
        method: str,
        endpoint: str,
        query: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        url = self._build_url(endpoint)
        try:
            response = requests.request(
                method=method,
                url=url,
                headers={
                    **self._headers,
                    **(headers or {}),
                },
                json=data,
                params=query,
                timeout=self._timeout,
            )

            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response is not None else 0
            response_body = ""

            if e.response is not None:
                response_body = e.response.text

            self._logger.error(f"HTTP error {status_code} on {method} {url}: {e}")

            if response_body:
                self._log_response_error(response_body)

            raise ProviderHTTPError(
                self.__class__.__name__,
                status_code,
                str(e),
                response_body,
            ) from e

        except requests.exceptions.RequestException as e:
            self._logger.error(f"Request error on {method} {url}: {e}")
            raise ProviderRequestError(str(e)) from e

    def _setup_headers(self, base_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
        }

        if base_headers:
            headers.update(base_headers)

        return headers

    def _validate_configuration(self) -> None:
        if not self._base_url:
            self._logger.error("Base URL not configured")
            raise ProviderRequestError("Base URL not configured")


__all__ = ["BaseProvider"]
