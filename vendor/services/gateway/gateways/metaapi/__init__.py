"""MetaAPI gateway implementation for MetaTrader integration."""

from typing import Any, Dict, List, Optional

from vendor.interfaces.gateway import GatewayInterface
from vendor.services.gateway.gateways.metaapi.components.account import AccountComponent
from vendor.services.gateway.gateways.metaapi.components.kline import KlineComponent
from vendor.services.gateway.gateways.metaapi.components.order import OrderComponent
from vendor.services.gateway.gateways.metaapi.components.position import PositionComponent
from vendor.services.gateway.gateways.metaapi.components.stream import StreamComponent
from vendor.services.gateway.gateways.metaapi.components.symbol import SymbolComponent
from vendor.services.gateway.gateways.metaapi.components.trade import TradeComponent
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
    via MetaAPI cloud service. Supports trading operations, position management,
    trade history retrieval, and historical kline data.

    Attributes:
        _config: MetaAPI configuration model with credentials and URLs.
        _account_component: Component for account information retrieval.
        _kline_component: Component for candlestick data retrieval.
        _order_component: Component for order management operations.
        _position_component: Component for position data retrieval.
        _symbol_component: Component for symbol information retrieval.
        _trade_component: Component for trade history retrieval.
        _log: Logging service instance.
    """

    _config: MetaApiConfigModel
    _account_component: AccountComponent
    _kline_component: KlineComponent
    _order_component: OrderComponent
    _position_component: PositionComponent
    _stream_component: StreamComponent
    _symbol_component: SymbolComponent
    _trade_component: TradeComponent
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
                - base_url: Optional custom base URL for market data API.
                - client_api_url: Optional custom base URL for client/trading API.
        """
        self._log = LoggingService()

        auth_token = kwargs.get("auth_token")
        account_id = kwargs.get("account_id")
        base_url = kwargs.get(
            "base_url",
            "https://mt-market-data-client-api-v1.new-york.agiliumtrade.ai",
        )
        client_api_url = kwargs.get(
            "client_api_url",
            "https://mt-client-api-v1.new-york.agiliumtrade.ai",
        )

        self._config = MetaApiConfigModel(
            auth_token=auth_token,
            account_id=account_id,
            base_url=base_url,
            client_api_url=client_api_url,
        )

        self._account_component = AccountComponent(
            config=self._config,
        )
        self._kline_component = KlineComponent(
            config=self._config,
        )
        self._order_component = OrderComponent(
            config=self._config,
        )
        self._position_component = PositionComponent(
            config=self._config,
        )
        self._stream_component = StreamComponent(
            config=self._config,
        )
        self._symbol_component = SymbolComponent(
            config=self._config,
        )
        self._trade_component = TradeComponent(
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
        """
        Cancel an existing pending order on MetaTrader via MetaAPI.

        Args:
            **kwargs: Keyword arguments:
                - order: GatewayOrderModel instance containing the order to cancel.

        Returns:
            GatewayOrderModel with updated status if cancellation was successful,
            None otherwise.
        """
        order = kwargs.get("order")

        if not order:
            self._log.error("order is required for cancel_order")
            return None

        return self._order_component.cancel_order(order=order)

    def get_account(
        self,
        **kwargs: Any,  # noqa: ARG002
    ) -> Optional[GatewayAccountModel]:
        """
        Retrieve account information from MetaAPI.

        Fetches account details including balance, equity, margin, and free margin.

        Args:
            **kwargs: Keyword arguments (reserved for future use).

        Returns:
            GatewayAccountModel if successful, None otherwise.
        """
        return self._account_component.get_account()

    def get_leverage_info(
        self,
        **kwargs: Any,
    ) -> Optional[GatewayLeverageInfoModel]:
        """
        Retrieve leverage information for a symbol.

        MetaAPI leverage is account-wide, not per-symbol.

        Args:
            **kwargs: Keyword arguments:
                - symbol: Trading pair symbol (e.g., "XAUUSD").

        Returns:
            GatewayLeverageInfoModel containing leverage information,
            or None if request fails.
        """
        symbol = kwargs.get("symbol")

        if not symbol:
            self._log.error("symbol is required for get_leverage_info")
            return None

        return self._symbol_component.get_leverage_info(symbol=symbol)

    def get_order(
        self,
        **kwargs: Any,
    ) -> Optional[GatewayOrderModel]:
        """
        Retrieve a single pending order by ID from MetaAPI.

        Args:
            **kwargs: Keyword arguments:
                - order_id: Order ID/ticket to retrieve.

        Returns:
            GatewayOrderModel if order was found, None otherwise.
        """
        order_id = kwargs.get("order_id")

        if not order_id:
            self._log.error("order_id is required for get_order")
            return None

        return self._order_component.get_order(order_id=str(order_id))

    def get_orders(
        self,
        **kwargs: Any,
    ) -> List[GatewayOrderModel]:
        """
        Retrieve pending orders from MetaAPI.

        Args:
            **kwargs: Keyword arguments:
                - symbol: Optional trading symbol to filter orders.

        Returns:
            List of GatewayOrderModel instances. Empty list if request fails
            or no pending orders exist.
        """
        symbol = kwargs.get("symbol")
        return self._order_component.get_orders(symbol=symbol)

    def get_positions(
        self,
        **kwargs: Any,
    ) -> List[GatewayPositionModel]:
        """
        Retrieve positions from MetaAPI.

        Args:
            **kwargs: Keyword arguments:
                - symbol: Optional trading symbol to filter positions (e.g., "XAUUSD").

        Returns:
            List of GatewayPositionModel instances. Empty list if request fails
            or no positions exist.
        """
        symbol = kwargs.get("symbol")
        return self._position_component.get_positions(symbol=symbol)

    def get_symbol_info(
        self,
        **kwargs: Any,
    ) -> Optional[GatewaySymbolInfoModel]:
        """
        Retrieve symbol specification for a given trading pair.

        Fetches symbol details including precision, min/max volume, tick size,
        and margin requirements from MetaAPI.

        Args:
            **kwargs: Keyword arguments:
                - symbol: Trading pair symbol (e.g., "XAUUSD", "EURUSD").

        Returns:
            GatewaySymbolInfoModel if successful, None otherwise.
        """
        symbol = kwargs.get("symbol")

        if not symbol:
            self._log.error("symbol is required for get_symbol_info")
            return None

        return self._symbol_component.get_symbol_info(symbol=symbol)

    def get_trades(
        self,
        **kwargs: Any,
    ) -> List[GatewayTradeModel]:
        """
        Retrieve trade history (deals) from MetaAPI.

        Args:
            **kwargs: Keyword arguments:
                - symbol: Optional trading symbol to filter trades.
                - start_time: Optional start datetime for trade history range.
                - end_time: Optional end datetime for trade history range.
                - position_id: Optional position ID to filter trades.
                - limit: Maximum number of trades to retrieve (default: 1000).

        Returns:
            List of GatewayTradeModel instances. Empty list if request fails
            or no trades found.
        """
        return self._trade_component.get_trades(
            symbol=kwargs.get("symbol"),
            start_time=kwargs.get("start_time"),
            end_time=kwargs.get("end_time"),
            position_id=kwargs.get("position_id"),
            limit=kwargs.get("limit", 1000),
        )

    def get_trading_fees(
        self,
        **kwargs: Any,
    ) -> Optional[GatewayTradingFeesModel]:
        """
        Retrieve trading fees for a symbol.

        MetaAPI does not provide a direct endpoint for trading fees.
        Returns a model with None values for commission rates.

        Args:
            **kwargs: Keyword arguments:
                - symbol: Trading pair symbol (e.g., "XAUUSD").

        Returns:
            GatewayTradingFeesModel with symbol, or None if symbol invalid.
        """
        symbol = kwargs.get("symbol")

        if not symbol:
            self._log.error("symbol is required for get_trading_fees")
            return None

        return self._symbol_component.get_trading_fees(symbol=symbol)

    def get_verification(
        self,
        **kwargs: Any,  # noqa: ARG002
    ) -> Dict[str, bool]:
        """
        Verify MetaAPI configuration and credentials.

        Performs checks to ensure the account is properly configured
        for trading, including credentials and trading permissions.

        Args:
            **kwargs: Keyword arguments (reserved for future use).

        Returns:
            Dictionary with verification status:
                - credentials_configured: Whether auth_token and account_id are set
                - trading_allowed: Whether trading is enabled on the account
                - has_balance: Whether account has positive balance
        """
        return self._account_component.get_verification()

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
        """
        Place a new order on MetaTrader via MetaAPI.

        Args:
            **kwargs: Keyword arguments:
                - symbol: Trading symbol (e.g., "XAUUSD").
                - side: Order side (OrderSide.BUY or OrderSide.SELL).
                - order_type: Order type (OrderType.MARKET).
                - volume: Order volume/quantity in lots.
                - price: Optional price (ignored for MARKET orders).
                - stop_loss: Optional stop loss price.
                - take_profit: Optional take profit price.
                - client_order_id: Optional custom client order ID.

        Returns:
            GatewayOrderModel if order was placed successfully, None otherwise.
        """
        symbol = kwargs.get("symbol")
        side = kwargs.get("side")
        order_type = kwargs.get("order_type")
        volume = kwargs.get("volume")

        if not symbol or not side or not order_type or not volume:
            self._log.error("symbol, side, order_type, and volume are required for place_order")
            return None

        return self._order_component.place_order(
            symbol=symbol,
            side=side,
            order_type=order_type,
            volume=volume,
            price=kwargs.get("price"),
            stop_loss=kwargs.get("stop_loss"),
            take_profit=kwargs.get("take_profit"),
            client_order_id=kwargs.get("client_order_id"),
        )

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
        """
        Stream real-time price data from MetaAPI via REST polling.

        Polls the readTick endpoint at regular intervals and invokes
        the callback with new tick data.

        Args:
            **kwargs: Keyword arguments:
                - symbols: List of trading symbols to stream (e.g., ["XAUUSD"]).
                - callback: Async callback function that receives TickModel instances.
                - poll_interval: Polling interval in seconds (default: 1.0, min: 0.5).
        """
        symbols = kwargs.get("symbols", [])
        callback = kwargs.get("callback")
        poll_interval = kwargs.get("poll_interval")

        if not symbols:
            self._log.error("symbols is required for stream")
            return

        if not callback:
            self._log.error("callback is required for stream")
            return

        await self._stream_component.stream(
            symbols=symbols,
            callback=callback,
            poll_interval=poll_interval,
        )

    async def stop_stream(self) -> None:
        """Stop the streaming connection."""
        await self._stream_component.stop()

    def close_position(
        self,
        **kwargs: Any,
    ) -> Optional[GatewayOrderModel]:
        """
        Close a position on MetaTrader via MetaAPI.

        Args:
            **kwargs: Keyword arguments:
                - position_id: Position ID to close.
                - volume: Optional volume to close (partial close).
                    If None, closes entire position.

        Returns:
            GatewayOrderModel representing the close order if successful,
            None otherwise.
        """
        position_id = kwargs.get("position_id")

        if not position_id:
            self._log.error("position_id is required for close_position")
            return None

        return self._order_component.close_position(
            position_id=str(position_id),
            volume=kwargs.get("volume"),
        )
