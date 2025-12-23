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
        json_body: Optional[Dict[str, Any]] = None,
        use_client_api: bool = False,
    ) -> Optional[Union[Dict[str, Any], List[Any]]]:
        """
        Execute authenticated request to MetaAPI.

        Args:
            method: HTTP method.
            endpoint: API endpoint path (without base URL).
            params: Optional query parameters.
            json_body: Optional JSON body for POST/PUT requests.
            use_client_api: If True, use client API URL instead of market data URL.

        Returns:
            JSON response or None if request fails.
        """
        if not self._config.auth_token:
            self._log.error("auth_token required for authenticated request")
            return None

        base_url = self._config.client_api_url if use_client_api else self._config.base_url
        url = f"{base_url}{endpoint}"

        return execute_request(
            method=method,
            url=url,
            auth_token=self._config.auth_token,
            params=params,
            json_body=json_body,
        )
