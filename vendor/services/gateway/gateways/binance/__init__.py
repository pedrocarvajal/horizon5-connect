"""Binance gateway implementation for historical kline retrieval."""

from typing import Any, Dict

from vendor.interfaces.gateway import GatewayInterface
from vendor.services.gateway.gateways.binance.components.kline import KlineComponent
from vendor.services.gateway.gateways.binance.models.config import BinanceConfigModel
from vendor.services.logging import LoggingService


class Binance(GatewayInterface):
    """Binance gateway implementation for backtest historical data retrieval."""

    _config: BinanceConfigModel
    _kline_component: KlineComponent
    _log: LoggingService

    def __init__(
        self,
        **kwargs: Any,  # noqa: ARG002
    ) -> None:
        """Initialize the Binance gateway with the public Futures API URL."""
        self._log = LoggingService()

        urls = self._build_urls()

        self._config = BinanceConfigModel(
            fapi_url=urls["fapi_url"],
        )

        self._kline_component = KlineComponent(
            config=self._config,
        )

    def get_klines(
        self,
        **kwargs: Any,
    ) -> None:
        """Get klines (candlestick data) from Binance."""
        self._kline_component.get_klines(**kwargs)

    def _build_urls(self) -> Dict[str, str]:
        """Return the Binance Futures public API URL."""
        return {
            "fapi_url": "https://fapi.binance.com/fapi/v1",
        }
