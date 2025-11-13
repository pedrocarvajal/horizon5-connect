from collections.abc import Callable
from typing import Any, Dict, List, Optional

from configs.gateways import GATEWAYS
from interfaces.gateway import GatewayInterface
from services.gateway.models.kline import KlineModel
from services.gateway.models.symbol_info import SymbolInfoModel
from services.gateway.models.trading_fees import TradingFeesModel
from services.logging import LoggingService


class GatewayService(GatewayInterface):
    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    _name: str
    _gateway: GatewayInterface
    _futures: bool
    _sandbox: bool

    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(
        self,
        gateway: str,
        **kwargs: Any,
    ) -> None:
        self._log = LoggingService()
        self._log.setup("gateway_service")

        self._gateways = GATEWAYS
        self._name = gateway
        self._futures = kwargs.get("futures", False)
        self._sandbox = kwargs.get("sandbox", False)

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
        *,
        callback: Callable[[List[KlineModel]], None],
        **kwargs: Any,
    ) -> None:
        self._gateway.get_klines(
            futures=self._futures,
            symbol=symbol,
            timeframe=timeframe,
            from_date=from_date,
            to_date=to_date,
            callback=callback,
            **kwargs,
        )

    def get_symbol_info(
        self,
        symbol: str,
    ) -> Optional[SymbolInfoModel]:
        return self._gateway.get_symbol_info(
            futures=self._futures,
            symbol=symbol,
        )

    def get_trading_fees(
        self,
        symbol: str,
    ) -> Optional[TradingFeesModel]:
        return self._gateway.get_trading_fees(
            futures=self._futures,
            symbol=symbol,
        )

    def get_leverage_info(
        self,
        symbol: str,
    ) -> Optional[Dict[str, Any]]:
        return self._gateway.get_leverage_info(
            futures=self._futures,
            symbol=symbol,
        )

    # ───────────────────────────────────────────────────────────
    # PRIVATE METHODS
    # ───────────────────────────────────────────────────────────
    def _setup(self) -> None:
        if self._name not in self._gateways:
            raise ValueError(f"Gateway {self._name} not found")

        self._log.info(f"Setting up gateway {self._name}")
        self._gateway = self._gateways[self._name]["class"](
            **self._gateways[self._name]["kwargs"],
            sandbox=self._sandbox,
        )

    # ───────────────────────────────────────────────────────────
    # GETTERS
    # ───────────────────────────────────────────────────────────
    @property
    def name(self) -> str:
        return self._name
