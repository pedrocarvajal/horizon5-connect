from typing import Any, Dict, Optional

from services.gateway.gateways.binance.helpers import execute_request
from services.gateway.gateways.binance.models.config import BinanceConfigModel
from services.logging import LoggingService


class BaseComponent:
    _config: BinanceConfigModel
    _log: LoggingService

    def __init__(
        self,
        config: BinanceConfigModel,
    ) -> None:
        self._config = config
        self._log = LoggingService()
        self._log.setup(self._get_log_name())

    def _get_log_name(self) -> str:
        class_name = self.__class__.__name__
        component_name = class_name.replace("Component", "").lower()

        return f"gateway_binance_{component_name}"

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
