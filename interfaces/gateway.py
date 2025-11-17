from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, Dict, List, Optional

from enums.order_side import OrderSide
from enums.order_type import OrderType
from services.gateway.models.gateway_account import GatewayAccountModel
from services.gateway.models.gateway_kline import GatewayKlineModel
from services.gateway.models.gateway_order import GatewayOrderModel
from services.gateway.models.gateway_symbol_info import GatewaySymbolInfoModel
from services.gateway.models.gateway_trading_fees import GatewayTradingFeesModel


class GatewayInterface(ABC):
    @abstractmethod
    def get_klines(
        self,
        futures: bool,
        symbol: str,
        timeframe: str,
        from_date: Optional[int],
        to_date: Optional[int],
        *,
        callback: Callable[[List[GatewayKlineModel]], None],
        **kwargs: Any,
    ) -> None:
        pass

    @abstractmethod
    def get_symbol_info(
        self,
        futures: bool,
        symbol: str,
    ) -> Optional[GatewaySymbolInfoModel]:
        pass

    @abstractmethod
    def get_trading_fees(
        self,
        futures: bool,
        symbol: str,
    ) -> Optional[GatewayTradingFeesModel]:
        pass

    @abstractmethod
    def get_leverage_info(
        self,
        futures: bool,
        symbol: str,
    ) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def stream(
        self,
        futures: bool,
        streams: List[str],
        callback: Callable[[Any], None],
    ) -> None:
        pass

    @abstractmethod
    def set_leverage(
        self,
        futures: bool,
        symbol: str,
        leverage: int,
    ) -> bool:
        pass

    @abstractmethod
    def open(
        self,
        futures: bool,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        volume: float,
        price: Optional[float] = None,
        client_order_id: Optional[str] = None,
        **kwargs: Any,
    ) -> Optional[GatewayOrderModel]:
        pass

    @abstractmethod
    def close(
        self,
        futures: bool,
        symbol: str,
        order_id: Optional[str] = None,
        client_order_id: Optional[str] = None,
        **kwargs: Any,
    ) -> Optional[GatewayOrderModel]:
        pass

    @abstractmethod
    def account(
        self,
        futures: bool,
        **kwargs: Any,
    ) -> Optional[GatewayAccountModel]:
        pass
