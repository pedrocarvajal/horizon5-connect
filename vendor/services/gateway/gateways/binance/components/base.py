"""Base component class for Binance API operations."""

from typing import Any, Dict, Optional

from vendor.services.gateway.gateways.binance.helpers import execute_request
from vendor.services.gateway.gateways.binance.models.config import BinanceConfigModel
from vendor.services.logging import LoggingService


class BaseComponent:
    """Base class providing common functionality for Binance API components."""

    _config: BinanceConfigModel
    _log: LoggingService

    def __init__(
        self,
        config: BinanceConfigModel,
    ) -> None:
        """Initialize the component with configuration."""
        self._config = config
        self._log = LoggingService()

    def _execute(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        if not self._config.api_key or not self._config.api_secret:
            self._log.error("API credentials required for authenticated request")
            return None

        return execute_request(
            method=method,
            url=url,
            api_key=self._config.api_key,
            api_secret=self._config.api_secret,
            params=params,
            log_error=self._log.error,
        )
