# Last coding review: 2025-11-17 17:00:40
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from services.gateway.models.gateway_account import GatewayAccountModel
from services.gateway.models.gateway_kline import GatewayKlineModel
from services.gateway.models.gateway_order import GatewayOrderModel
from services.gateway.models.gateway_symbol_info import GatewaySymbolInfoModel
from services.gateway.models.gateway_trading_fees import GatewayTradingFeesModel


class BaseGatewayAdapter(ABC):
    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    @abstractmethod
    def adapt_klines_batch(
        self,
        response: List[Any],
        symbol: str,
    ) -> List[GatewayKlineModel]:
        pass

    @abstractmethod
    def adapt_symbol_info(
        self,
        response: Dict[str, Any],
    ) -> Optional[GatewaySymbolInfoModel]:
        pass

    @abstractmethod
    def adapt_trading_fees(
        self,
        response: Dict[str, Any],
        futures: bool,
    ) -> Optional[GatewayTradingFeesModel]:
        pass

    @abstractmethod
    def adapt_order_response(
        self,
        response: Dict[str, Any],
        symbol: str,
    ) -> Optional[GatewayOrderModel]:
        pass

    @abstractmethod
    def adapt_account_response(
        self,
        response: Dict[str, Any],
        futures: bool,
    ) -> Optional[GatewayAccountModel]:
        pass

    @abstractmethod
    def validate_response(
        self,
        response: Any,
    ) -> bool:
        pass
