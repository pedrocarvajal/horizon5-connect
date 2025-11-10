from collections.abc import Callable
from typing import Any, Dict, List, Optional

from configs.gateways import GATEWAYS
from interfaces.gateway import GatewayInterface
from services.logging import LoggingService


class GatewayService(GatewayInterface):
    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    _name: str
    _gateway: GatewayInterface

    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(self, gateway: str) -> None:
        self._gateways = GATEWAYS
        self._name = gateway

        self._log = LoggingService()
        self._log.setup("gateway_service")

        self._setup()

    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def get_klines(
        self,
        symbol: str,
        timeframe: str,
        from_date: Optional[int],
        to_date: Optional[int],
        callback: Callable[[List[Dict[str, Any]]], None],
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

    # ───────────────────────────────────────────────────────────
    # PRIVATE METHODS
    # ───────────────────────────────────────────────────────────
    def _setup(self) -> None:
        if self._name not in self._gateways:
            raise ValueError(f"Gateway {self._name} not found")

        self._log.info(f"Setting up gateway {self._name}")
        self._gateway = self._gateways[self._name]["class"](
            **self._gateways[self._name]["kwargs"]
        )

    # ───────────────────────────────────────────────────────────
    # GETTERS
    # ───────────────────────────────────────────────────────────
    @property
    def name(self) -> str:
        return self._name

    @property
    def configs(self) -> Dict[str, Any]:
        return {
            "margin_liquidation_ratio": 0.2,
        }
