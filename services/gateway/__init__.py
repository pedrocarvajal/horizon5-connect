from collections.abc import Callable
from typing import Any, Dict, List, Optional

from configs.gateways import GATEWAYS
from enums.order_side import OrderSide
from enums.order_type import OrderType
from interfaces.gateway import GatewayInterface
from services.gateway.models.gateway_account import GatewayAccountModel
from services.gateway.models.gateway_kline import GatewayKlineModel
from services.gateway.models.gateway_order import GatewayOrderModel
from services.gateway.models.gateway_symbol_info import GatewaySymbolInfoModel
from services.gateway.models.gateway_trading_fees import GatewayTradingFeesModel
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
        callback: Callable[[List[GatewayKlineModel]], None],
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
    ) -> Optional[GatewaySymbolInfoModel]:
        return self._gateway.get_symbol_info(
            futures=self._futures,
            symbol=symbol,
        )

    def get_trading_fees(
        self,
        symbol: str,
    ) -> Optional[GatewayTradingFeesModel]:
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

    async def stream(
        self,
        streams: List[str],
        callback: Callable[[Any], None],
    ) -> None:
        await self._gateway.stream(
            futures=self._futures,
            streams=streams,
            callback=callback,
        )

    def open(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        volume: float,
        price: Optional[float] = None,
        client_order_id: Optional[str] = None,
        **kwargs: Any,
    ) -> Optional[GatewayOrderModel]:
        return self._gateway.open(
            futures=self._futures,
            symbol=symbol,
            side=side,
            order_type=order_type,
            volume=volume,
            price=price,
            client_order_id=client_order_id,
            **kwargs,
        )

    def set_leverage(
        self,
        symbol: str,
        leverage: int,
    ) -> bool:
        return self._gateway.set_leverage(
            futures=self._futures,
            symbol=symbol,
            leverage=leverage,
        )

    def account(
        self,
        **kwargs: Any,
    ) -> Optional[GatewayAccountModel]:
        return self._gateway.account(
            futures=self._futures,
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
            **self._gateways[self._name]["kwargs"],
        )

    # ───────────────────────────────────────────────────────────
    # GETTERS
    # ───────────────────────────────────────────────────────────
    @property
    def name(self) -> str:
        return self._name
