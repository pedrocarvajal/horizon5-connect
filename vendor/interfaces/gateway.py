"""Gateway interface for exchange integrations."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from vendor.services.gateway.models.gateway_account import GatewayAccountModel
from vendor.services.gateway.models.gateway_leverage_info import GatewayLeverageInfoModel
from vendor.services.gateway.models.gateway_order import GatewayOrderModel
from vendor.services.gateway.models.gateway_position import GatewayPositionModel
from vendor.services.gateway.models.gateway_symbol_info import GatewaySymbolInfoModel
from vendor.services.gateway.models.gateway_trade import GatewayTradeModel
from vendor.services.gateway.models.gateway_trading_fees import GatewayTradingFeesModel


class GatewayInterface(ABC):
    """Abstract interface for exchange/gateway integrations."""

    @abstractmethod
    def get_klines(
        self,
        **kwargs: Any,
    ) -> None:
        """Retrieve candlestick/kline data from exchange."""
        pass

    @abstractmethod
    def get_symbol_info(
        self,
        **kwargs: Any,
    ) -> Optional[GatewaySymbolInfoModel]:
        """Get trading symbol information and specifications."""
        pass

    @abstractmethod
    def get_trading_fees(
        self,
        **kwargs: Any,
    ) -> Optional[GatewayTradingFeesModel]:
        """Get trading fees for symbol."""
        pass

    @abstractmethod
    def get_leverage_info(
        self,
        **kwargs: Any,
    ) -> Optional[GatewayLeverageInfoModel]:
        """Get leverage information for symbol."""
        pass

    @abstractmethod
    async def stream(
        self,
        **kwargs: Any,
    ) -> None:
        """Stream real-time market data."""
        pass

    @abstractmethod
    def set_leverage(
        self,
        **kwargs: Any,
    ) -> bool:
        """Set leverage for trading symbol."""
        pass

    @abstractmethod
    def place_order(
        self,
        **kwargs: Any,
    ) -> Optional[GatewayOrderModel]:
        """Place new order on exchange."""
        pass

    @abstractmethod
    def get_account(
        self,
        **kwargs: Any,
    ) -> Optional[GatewayAccountModel]:
        """Get account information and balances."""
        pass

    @abstractmethod
    def get_order(
        self,
        **kwargs: Any,
    ) -> Optional[GatewayOrderModel]:
        """Get order details by ID."""
        pass

    @abstractmethod
    def cancel_order(
        self,
        **kwargs: Any,
    ) -> Optional[GatewayOrderModel]:
        """Cancel existing order."""
        pass

    @abstractmethod
    def modify_order(
        self,
        **kwargs: Any,
    ) -> Optional[GatewayOrderModel]:
        """Modify existing order."""
        pass

    @abstractmethod
    def get_orders(
        self,
        **kwargs: Any,
    ) -> List[GatewayOrderModel]:
        """Get list of orders."""
        pass

    @abstractmethod
    def get_verification(
        self,
        **kwargs: Any,
    ) -> Dict[str, bool]:
        """Verify gateway configuration and permissions."""
        pass

    @abstractmethod
    def get_trades(
        self,
        **kwargs: Any,
    ) -> List[GatewayTradeModel]:
        """Get list of executed trades."""
        pass

    @abstractmethod
    def get_positions(
        self,
        **kwargs: Any,
    ) -> List[GatewayPositionModel]:
        """Get list of open positions."""
        pass
