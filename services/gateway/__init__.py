from collections.abc import Callable
from typing import Any

from configs.gateways import GATEWAYS
from interfaces.gateway import GatewayInterface
from models.candlestick import CandlestickModel
from services.logging import LoggingService


class GatewayService(GatewayInterface):
    _name: str
    _credentials: dict[str, str]
    _gateway: GatewayInterface

    def __init__(self, gateway: str) -> None:
        self._gateways = GATEWAYS
        self._name = gateway

        self._log = LoggingService()
        self._log.setup("gateway_service")

        self._setup()

    def _setup(self) -> None:
        if self._name not in self._gateways:
            raise ValueError(f"Gateway {self._name} not found")

        self._log.info(f"Setting up gateway {self._name}")
        self._gateway = self._gateways[self._name]["class"](
            **self._gateways[self._name]["variables"]
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

    @property
    def name(self) -> str:
        return self._name
