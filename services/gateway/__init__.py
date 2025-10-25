from collections.abc import Callable
from typing import Any

from configs.gateways import GATEWAYS
from interfaces.gateway import GatewayInterface
from models.candlestick import CandlestickModel
from services.logging import LoggingService


class GatewayService(GatewayInterface):
    _gateway_name: str
    _gateway_credentials: dict[str, str]
    _gateway: GatewayInterface

    def __init__(self, gateway: str) -> None:
        self._gateways = GATEWAYS
        self._gateway_name = gateway

        self._log = LoggingService()
        self._log.setup("gateway_service")

        self._setup()

    def _setup(self) -> None:
        if self._gateway_name not in self._gateways:
            raise ValueError(f"Gateway {self._gateway_name} not found")

        self._log.info(f"Setting up gateway {self._gateway_name}")
        self._gateway = self._gateways[self._gateway_name]["class"](
            **self._gateways[self._gateway_name]["variables"]
        )

    def get_klines(
        self,
        symbol: str,
        timeframe: str,
        from_date: int | None,
        to_date: int | None,
        callback: Callable[[list[CandlestickModel]], None],
        **kwargs: Any,
    ) -> None:
        self._gateway.get_klines(
            symbol=symbol,
            timeframe=timeframe,
            from_date=from_date,
            to_date=to_date,
            callback=callback,
            **kwargs,
        )
