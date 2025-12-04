"""Provider exception classes for HTTP and request errors."""


class ProviderError(Exception):
    """Base exception for provider-related errors."""

    pass


class ProviderHTTPError(ProviderError):
    """HTTP error from provider API request.

    Attributes:
        service_name: Name of the provider service.
        status_code: HTTP status code.
        response_body: Raw response body from the API.
    """

    def __init__(self, service_name: str, status_code: int, message: str, response_body: str = "") -> None:
        """Initialize HTTP error with service name, status code, and message.

        Args:
            service_name: Name of the provider service.
            status_code: HTTP status code.
            message: Error message.
            response_body: Raw response body from the API.
        """
        self.service_name = service_name
        self.status_code = status_code
        self.response_body = response_body
        error_message = f"{service_name} API request failed with status {status_code}: {message}"
        if response_body:
            error_message = f"{error_message}\nResponse: {response_body}"
        super().__init__(error_message)


class ProviderRequestError(ProviderError):
    """Request error from provider API operation."""

    def __init__(self, message: str) -> None:
        """Initialize request error with message."""
        super().__init__(message)


__all__ = ["ProviderError", "ProviderHTTPError", "ProviderRequestError"]
