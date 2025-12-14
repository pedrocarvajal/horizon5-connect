"""MetaAPI gateway implementation for MetaTrader integration."""

from typing import Any, Dict, List, Optional

from vendor.interfaces.gateway import GatewayInterface
from vendor.services.gateway.gateways.metaapi.components.kline import KlineComponent
from vendor.services.gateway.gateways.metaapi.models.config import MetaApiConfigModel
from vendor.services.gateway.models.gateway_account import GatewayAccountModel
from vendor.services.gateway.models.gateway_leverage_info import GatewayLeverageInfoModel
from vendor.services.gateway.models.gateway_order import GatewayOrderModel
from vendor.services.gateway.models.gateway_position import GatewayPositionModel
from vendor.services.gateway.models.gateway_symbol_info import GatewaySymbolInfoModel
from vendor.services.gateway.models.gateway_trade import GatewayTradeModel
from vendor.services.gateway.models.gateway_trading_fees import GatewayTradingFeesModel
from vendor.services.logging import LoggingService


class MetaApi(GatewayInterface):
    """
    MetaAPI gateway implementation for MetaTrader operations.

    Implements GatewayInterface to provide access to MetaTrader accounts
    via MetaAPI cloud service. Currently supports historical kline data
    retrieval for backtesting purposes.

    Attributes:
        _config: MetaAPI configuration model with credentials and URLs.
        _kline_component: Component for candlestick data retrieval.
        _log: Logging service instance.
    """

    _config: MetaApiConfigModel
    _kline_component: KlineComponent
    _log: LoggingService

    def __init__(
        self,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the MetaAPI gateway.

        Args:
            **kwargs: Keyword arguments for gateway configuration:
                - auth_token: MetaAPI JWT authentication token.
                - account_id: MetaTrader account ID registered with MetaAPI.
                - base_url: Optional custom base URL for MetaAPI.
        """
        self._log = LoggingService()

        auth_token = kwargs.get("auth_token")
        account_id = kwargs.get("account_id")
        base_url = kwargs.get(
            "base_url",
            "https://mt-market-data-client-api-v1.new-york.agiliumtrade.ai",
        )

        self._config = MetaApiConfigModel(
            auth_token=auth_token,
            account_id=account_id,
            base_url=base_url,
        )

        self._kline_component = KlineComponent(
            config=self._config,
        )

    def get_klines(
        self,
        **kwargs: Any,
    ) -> None:
        """
        Get klines (candlestick data) from MetaAPI.

        Args:
            **kwargs: Keyword arguments for klines retrieval:
                - symbol: Trading symbol (e.g., "XAUUSD", "EURUSD").
                - timeframe: Kline interval ("1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w", "1mn").
                - from_date: Start time in Unix timestamp seconds.
                - to_date: End time in Unix timestamp seconds.
                - callback: Callback function to receive kline batches.
                - limit: Number of klines per request (optional, default: 1000).
        """
        self._kline_component.get_klines(**kwargs)

    def cancel_order(
        self,
        **kwargs: Any,
    ) -> Optional[GatewayOrderModel]:
        """Cancel order - not implemented for MetaAPI."""
        raise NotImplementedError("cancel_order not implemented for MetaAPI")

    def get_account(
        self,
        **kwargs: Any,
    ) -> Optional[GatewayAccountModel]:
        """Get account - not implemented for MetaAPI."""
        raise NotImplementedError("get_account not implemented for MetaAPI")

    def get_leverage_info(
        self,
        **kwargs: Any,
    ) -> Optional[GatewayLeverageInfoModel]:
        """Get leverage info - not implemented for MetaAPI."""
        raise NotImplementedError("get_leverage_info not implemented for MetaAPI")

    def get_order(
        self,
        **kwargs: Any,
    ) -> Optional[GatewayOrderModel]:
        """Get order - not implemented for MetaAPI."""
        raise NotImplementedError("get_order not implemented for MetaAPI")

    def get_orders(
        self,
        **kwargs: Any,
    ) -> List[GatewayOrderModel]:
        """Get orders - not implemented for MetaAPI."""
        raise NotImplementedError("get_orders not implemented for MetaAPI")

    def get_positions(
        self,
        **kwargs: Any,
    ) -> List[GatewayPositionModel]:
        """Get positions - not implemented for MetaAPI."""
        raise NotImplementedError("get_positions not implemented for MetaAPI")

    def get_symbol_info(
        self,
        **kwargs: Any,
    ) -> Optional[GatewaySymbolInfoModel]:
        """Get symbol info - not implemented for MetaAPI."""
        raise NotImplementedError("get_symbol_info not implemented for MetaAPI")

    def get_trades(
        self,
        **kwargs: Any,
    ) -> List[GatewayTradeModel]:
        """Get trades - not implemented for MetaAPI."""
        raise NotImplementedError("get_trades not implemented for MetaAPI")

    def get_trading_fees(
        self,
        **kwargs: Any,
    ) -> Optional[GatewayTradingFeesModel]:
        """Get trading fees - not implemented for MetaAPI."""
        raise NotImplementedError("get_trading_fees not implemented for MetaAPI")

    def get_verification(
        self,
        **kwargs: Any,
    ) -> Dict[str, bool]:
        """Get verification - not implemented for MetaAPI."""
        raise NotImplementedError("get_verification not implemented for MetaAPI")

    def modify_order(
        self,
        **kwargs: Any,
    ) -> Optional[GatewayOrderModel]:
        """Modify order - not implemented for MetaAPI."""
        raise NotImplementedError("modify_order not implemented for MetaAPI")

    def place_order(
        self,
        **kwargs: Any,
    ) -> Optional[GatewayOrderModel]:
        """Place order - not implemented for MetaAPI."""
        raise NotImplementedError("place_order not implemented for MetaAPI")

    def set_leverage(
        self,
        **kwargs: Any,
    ) -> bool:
        """Set leverage - not implemented for MetaAPI."""
        raise NotImplementedError("set_leverage not implemented for MetaAPI")

    async def stream(
        self,
        **kwargs: Any,
    ) -> None:
        """Stream data - not implemented for MetaAPI."""
        raise NotImplementedError("stream not implemented for MetaAPI")
