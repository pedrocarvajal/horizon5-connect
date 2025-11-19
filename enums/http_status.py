# Code reviewed on 2025-11-19 by pedrocarvajal

from enum import Enum, unique


@unique
class HttpStatus(Enum):
    """
    Represents HTTP status codes with their descriptions.

    This enum provides standard HTTP status codes used throughout the system
    for API responses and error handling. Status codes are grouped by their
    meaning: success (2xx), client errors (4xx), and server errors (5xx).

    The enum includes helper properties to check status code categories:
    - is_success: Checks if status is in the 2xx range
    - is_client_error: Checks if status is in the 4xx range
    - is_server_error: Checks if status is in the 5xx range
    """

    OK = 200
    CREATED = 201
    ACCEPTED = 202
    NO_CONTENT = 204
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    CONFLICT = 409
    UNPROCESSABLE_ENTITY = 422
    TOO_MANY_REQUESTS = 429
    INTERNAL_SERVER_ERROR = 500
    BAD_GATEWAY = 502
    SERVICE_UNAVAILABLE = 503
    GATEWAY_TIMEOUT = 504

    @property
    def is_success(self) -> bool:
        """
        Check if status code represents a successful response.

        Returns:
            bool: True if status is 2xx, False otherwise.
        """
        return 200 <= self.value < 300

    @property
    def is_client_error(self) -> bool:
        """
        Check if status code represents a client error.

        Returns:
            bool: True if status is 4xx, False otherwise.
        """
        return 400 <= self.value < 500

    @property
    def is_server_error(self) -> bool:
        """
        Check if status code represents a server error.

        Returns:
            bool: True if status is 5xx, False otherwise.
        """
        return 500 <= self.value < 600

    @staticmethod
    def is_success_code(status_code: int) -> bool:
        """
        Check if a status code represents a successful response.

        Args:
            status_code: HTTP status code as integer.

        Returns:
            bool: True if status is 2xx, False otherwise.
        """
        return 200 <= status_code < 300

    @staticmethod
    def is_client_error_code(status_code: int) -> bool:
        """
        Check if a status code represents a client error.

        Args:
            status_code: HTTP status code as integer.

        Returns:
            bool: True if status is 4xx, False otherwise.
        """
        return 400 <= status_code < 500

    @staticmethod
    def is_server_error_code(status_code: int) -> bool:
        """
        Check if a status code represents a server error.

        Args:
            status_code: HTTP status code as integer.

        Returns:
            bool: True if status is 5xx, False otherwise.
        """
        return 500 <= status_code < 600
