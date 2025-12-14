"""Base component class for MetaAPI operations."""

from typing import Any, Dict, List, Optional, Union

from vendor.services.gateway.gateways.metaapi.helpers import execute_request
from vendor.services.gateway.gateways.metaapi.models.config import MetaApiConfigModel
from vendor.services.logging import LoggingService


class BaseComponent:
    """Base class providing common functionality for MetaAPI components."""

    _config: MetaApiConfigModel
    _log: LoggingService

    def __init__(
        self,
        config: MetaApiConfigModel,
    ) -> None:
        """Initialize the component with configuration."""
        self._config = config
        self._log = LoggingService()

    def _execute(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Optional[Union[Dict[str, Any], List[Any]]]:
        """
        Execute authenticated request to MetaAPI.

        Args:
            method: HTTP method.
            endpoint: API endpoint path (without base URL).
            params: Optional query parameters.

        Returns:
            JSON response or None if request fails.
        """
        if not self._config.auth_token:
            self._log.error("auth_token required for authenticated request")
            return None

        url = f"{self._config.base_url}{endpoint}"

        return execute_request(
            method=method,
            url=url,
            auth_token=self._config.auth_token,
            params=params,
            log_error=self._log.error,
        )
