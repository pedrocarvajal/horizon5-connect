from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from services.gateway.models.gateway_account import GatewayAccountModel
from services.gateway.models.gateway_leverage_info import GatewayLeverageInfoModel
from services.gateway.models.gateway_order import GatewayOrderModel
from services.gateway.models.gateway_position import GatewayPositionModel
from services.gateway.models.gateway_symbol_info import GatewaySymbolInfoModel
from services.gateway.models.gateway_trade import GatewayTradeModel
from services.gateway.models.gateway_trading_fees import GatewayTradingFeesModel


class GatewayInterface(ABC):
    @abstractmethod
    def get_klines(
        self,
        **kwargs: Any,
    ) -> None:
        pass

    @abstractmethod
    def get_symbol_info(
        self,
        **kwargs: Any,
    ) -> Optional[GatewaySymbolInfoModel]:
        pass

    @abstractmethod
    def get_trading_fees(
        self,
        **kwargs: Any,
    ) -> Optional[GatewayTradingFeesModel]:
        pass

    @abstractmethod
    def get_leverage_info(
        self,
        **kwargs: Any,
    ) -> Optional[GatewayLeverageInfoModel]:
        pass

    @abstractmethod
    async def stream(
        self,
        **kwargs: Any,
    ) -> None:
        pass

    @abstractmethod
    def set_leverage(
        self,
        **kwargs: Any,
    ) -> bool:
        pass

    @abstractmethod
    def place_order(
        self,
        **kwargs: Any,
    ) -> Optional[GatewayOrderModel]:
        pass

    @abstractmethod
    def get_account(
        self,
        **kwargs: Any,
    ) -> Optional[GatewayAccountModel]:
        pass

    @abstractmethod
    def get_order(
        self,
        **kwargs: Any,
    ) -> Optional[GatewayOrderModel]:
        pass

    @abstractmethod
    def cancel_order(
        self,
        **kwargs: Any,
    ) -> Optional[GatewayOrderModel]:
        pass

    @abstractmethod
    def modify_order(
        self,
        **kwargs: Any,
    ) -> Optional[GatewayOrderModel]:
        pass

    @abstractmethod
    def get_orders(
        self,
        **kwargs: Any,
    ) -> List[GatewayOrderModel]:
        pass

    @abstractmethod
    def get_verification(
        self,
        **kwargs: Any,
    ) -> Dict[str, bool]:
        pass

    @abstractmethod
    def get_trades(
        self,
        **kwargs: Any,
    ) -> List[GatewayTradeModel]:
        pass

    @abstractmethod
    def get_positions(
        self,
        **kwargs: Any,
    ) -> List[GatewayPositionModel]:
        pass
