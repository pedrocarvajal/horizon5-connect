# Code reviewed on 2025-11-19 by pedrocarvajal

from typing import Any, Dict, List, Optional

from interfaces.gateway import GatewayInterface
from services.gateway.gateways.binance.components.account import AccountComponent
from services.gateway.gateways.binance.components.kline import KlineComponent
from services.gateway.gateways.binance.components.order import OrderComponent
from services.gateway.gateways.binance.components.position import PositionComponent
from services.gateway.gateways.binance.components.stream import StreamComponent
from services.gateway.gateways.binance.components.symbol import SymbolComponent
from services.gateway.gateways.binance.components.trade import TradeComponent
from services.gateway.gateways.binance.models.config import BinanceConfigModel
from services.gateway.models.gateway_account import GatewayAccountModel
from services.gateway.models.gateway_leverage_info import GatewayLeverageInfoModel
from services.gateway.models.gateway_order import GatewayOrderModel
from services.gateway.models.gateway_position import GatewayPositionModel
from services.gateway.models.gateway_symbol_info import GatewaySymbolInfoModel
from services.gateway.models.gateway_trade import GatewayTradeModel
from services.gateway.models.gateway_trading_fees import GatewayTradingFeesModel
from services.logging import LoggingService


class Binance(GatewayInterface):
    """
    Binance gateway implementation for trading operations.

    This class implements the GatewayInterface to provide access to Binance
    Futures API functionality. It acts as a facade that delegates operations
    to specialized component classes, each handling a specific domain of
    the Binance API (account, orders, positions, trades, symbols, klines, streams).

    The gateway supports both production and sandbox/testnet environments,
    automatically configuring API endpoints based on the sandbox parameter.

    Attributes:
        _config: Binance configuration model containing API credentials and URLs.
        _account_component: Component for account-related operations.
        _kline_component: Component for candlestick/klines data retrieval.
        _order_component: Component for order management (place, cancel, modify).
        _position_component: Component for position management.
        _stream_component: Component for WebSocket streaming operations.
        _symbol_component: Component for symbol information and leverage management.
        _trade_component: Component for trade history retrieval.
        _log: Logging service instance for logging operations.
    """

    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    _config: BinanceConfigModel
    _account_component: AccountComponent
    _kline_component: KlineComponent
    _order_component: OrderComponent
    _position_component: PositionComponent
    _stream_component: StreamComponent
    _symbol_component: SymbolComponent
    _trade_component: TradeComponent
    _log: LoggingService

    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(
        self,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the Binance gateway.

        Args:
            **kwargs: Keyword arguments for gateway configuration. Supported keys:
                - sandbox: Whether to use sandbox/testnet mode (default: False).
                - api_key: Binance API key (required).
                - api_secret: Binance API secret (required).
        """
        self._log = LoggingService()
        self._log.setup("gateway_binance")

        sandbox = kwargs.get("sandbox", False)
        api_key = kwargs.get("api_key", "")
        api_secret = kwargs.get("api_secret", "")
        urls = self._build_urls(sandbox=sandbox)

        self._config = BinanceConfigModel(
            api_key=api_key,
            api_secret=api_secret,
            fapi_url=urls["fapi_url"],
            fapi_v2_url=urls["fapi_v2_url"],
            fapi_ws_url=urls["fapi_ws_url"],
            sandbox=sandbox,
        )

        self._order_component = OrderComponent(
            config=self._config,
        )

        self._position_component = PositionComponent(
            config=self._config,
        )

        self._trade_component = TradeComponent(
            config=self._config,
        )

        self._stream_component = StreamComponent(
            config=self._config,
        )

        self._kline_component = KlineComponent(
            config=self._config,
        )

        self._symbol_component = SymbolComponent(
            config=self._config,
        )

        self._account_component = AccountComponent(
            config=self._config,
        )

    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def get_klines(
        self,
        **kwargs: Any,
    ) -> None:
        """
        Get klines (candlestick data) from Binance.

        Args:
            **kwargs: Keyword arguments for klines retrieval. Common arguments include:
                - symbol: Trading symbol (e.g., "BTCUSDT").
                - interval: Kline interval (e.g., "1m", "5m", "1h", "1d").
                - start_time: Start time in milliseconds (optional).
                - end_time: End time in milliseconds (optional).
                - limit: Number of klines to retrieve (optional, default: 500).
        """
        self._kline_component.get_klines(**kwargs)

    def get_symbol_info(
        self,
        **kwargs: Any,
    ) -> Optional[GatewaySymbolInfoModel]:
        """
        Get symbol information from Binance.

        Args:
            **kwargs: Keyword arguments for symbol info retrieval. Typically includes:
                - symbol: Trading symbol (e.g., "BTCUSDT").

        Returns:
            GatewaySymbolInfoModel instance containing symbol information,
            or None if the symbol is not found or an error occurs.
        """
        return self._symbol_component.get_symbol_info(**kwargs)

    def get_trading_fees(
        self,
        **kwargs: Any,
    ) -> Optional[GatewayTradingFeesModel]:
        """
        Get trading fees information from Binance.

        Args:
            **kwargs: Keyword arguments for trading fees retrieval. Typically includes:
                - symbol: Trading symbol (e.g., "BTCUSDT").

        Returns:
            GatewayTradingFeesModel instance containing trading fees information,
            or None if the information cannot be retrieved or an error occurs.
        """
        return self._symbol_component.get_trading_fees(**kwargs)

    def get_leverage_info(
        self,
        **kwargs: Any,
    ) -> Optional[GatewayLeverageInfoModel]:
        """
        Get leverage information from Binance.

        Args:
            **kwargs: Keyword arguments for leverage info retrieval. Typically includes:
                - symbol: Trading symbol (e.g., "BTCUSDT").

        Returns:
            GatewayLeverageInfoModel instance containing leverage information,
            or None if the information cannot be retrieved or an error occurs.
        """
        return self._symbol_component.get_leverage_info(**kwargs)

    async def stream(
        self,
        **kwargs: Any,
    ) -> None:
        """
        Stream real-time data from Binance via WebSocket.

        This is an async method that establishes a WebSocket connection
        to stream market data, order updates, or other real-time information.

        Args:
            **kwargs: Keyword arguments for streaming. Common arguments include:
                - symbols: List of trading symbols to stream.
                - streams: List of stream names to subscribe to.
                - callbacks: Callback functions for handling stream events.

        Note:
            This method should be awaited and will run until the stream
            is closed or an error occurs.
        """
        await self._stream_component.stream(**kwargs)

    def place_order(
        self,
        **kwargs: Any,
    ) -> Optional[GatewayOrderModel]:
        """
        Place a new order on Binance.

        Args:
            **kwargs: Keyword arguments for order placement. Common arguments include:
                - symbol: Trading symbol (e.g., "BTCUSDT").
                - side: Order side (BUY or SELL).
                - order_type: Order type (MARKET, LIMIT, STOP_LOSS, etc.).
                - volume: Order volume/quantity.
                - price: Order price (required for LIMIT orders).
                - stop_price: Stop price (required for STOP_LOSS orders).
                - client_order_id: Optional client-side order identifier.

        Returns:
            GatewayOrderModel instance containing the placed order information,
            or None if the order placement fails or an error occurs.
        """
        return self._order_component.place_order(**kwargs)

    def cancel_order(
        self,
        **kwargs: Any,
    ) -> Optional[GatewayOrderModel]:
        """
        Cancel an existing order on Binance.

        Args:
            **kwargs: Keyword arguments for order cancellation. Common arguments include:
                - symbol: Trading symbol (e.g., "BTCUSDT").
                - order_id: Binance order ID.
                - client_order_id: Client-side order identifier.

        Returns:
            GatewayOrderModel instance containing the cancelled order information,
            or None if the cancellation fails or an error occurs.
        """
        return self._order_component.cancel_order(**kwargs)

    def modify_order(
        self,
        **kwargs: Any,
    ) -> Optional[GatewayOrderModel]:
        """
        Modify an existing order on Binance.

        Args:
            **kwargs: Keyword arguments for order modification. Common arguments include:
                - symbol: Trading symbol (e.g., "BTCUSDT").
                - order_id: Binance order ID.
                - client_order_id: Client-side order identifier.
                - volume: New order volume/quantity.
                - price: New order price.

        Returns:
            GatewayOrderModel instance containing the modified order information,
            or None if the modification fails or an error occurs.
        """
        return self._order_component.modify_order(**kwargs)

    def set_leverage(
        self,
        **kwargs: Any,
    ) -> bool:
        """
        Set leverage for a trading symbol on Binance.

        Args:
            **kwargs: Keyword arguments for leverage setting. Common arguments include:
                - symbol: Trading symbol (e.g., "BTCUSDT").
                - leverage: Leverage value to set.

        Returns:
            True if leverage was set successfully, False otherwise.
        """
        return self._symbol_component.set_leverage(**kwargs)

    def get_account(
        self,
        **kwargs: Any,
    ) -> Optional[GatewayAccountModel]:
        """
        Get account information from Binance.

        Args:
            **kwargs: Keyword arguments for account retrieval. Typically empty,
                but may include additional parameters for filtering.

        Returns:
            GatewayAccountModel instance containing account information,
            or None if the information cannot be retrieved or an error occurs.
        """
        return self._account_component.get_account(**kwargs)

    def get_orders(
        self,
        **kwargs: Any,
    ) -> List[GatewayOrderModel]:
        """
        Get list of orders from Binance.

        Args:
            **kwargs: Keyword arguments for orders retrieval. Common arguments include:
                - symbol: Trading symbol (e.g., "BTCUSDT") to filter orders.
                - order_id: Optional order ID to filter.
                - start_time: Start time in milliseconds (optional).
                - end_time: End time in milliseconds (optional).
                - limit: Maximum number of orders to retrieve (optional).

        Returns:
            List of GatewayOrderModel instances containing order information.
            Returns empty list if no orders are found or an error occurs.
        """
        return self._order_component.get_orders(**kwargs)

    def get_order(
        self,
        **kwargs: Any,
    ) -> Optional[GatewayOrderModel]:
        """
        Get a specific order from Binance.

        Args:
            **kwargs: Keyword arguments for order retrieval. Common arguments include:
                - symbol: Trading symbol (e.g., "BTCUSDT").
                - order_id: Binance order ID.
                - client_order_id: Client-side order identifier.

        Returns:
            GatewayOrderModel instance containing order information,
            or None if the order is not found or an error occurs.
        """
        return self._order_component.get_order(**kwargs)

    def get_trades(
        self,
        **kwargs: Any,
    ) -> List[GatewayTradeModel]:
        """
        Get trade history from Binance.

        Args:
            **kwargs: Keyword arguments for trades retrieval. Common arguments include:
                - symbol: Trading symbol (e.g., "BTCUSDT") to filter trades.
                - start_time: Start time in milliseconds (optional).
                - end_time: End time in milliseconds (optional).
                - limit: Maximum number of trades to retrieve (optional).

        Returns:
            List of GatewayTradeModel instances containing trade information.
            Returns empty list if no trades are found or an error occurs.
        """
        return self._trade_component.get_trades(**kwargs)

    def get_positions(
        self,
        **kwargs: Any,
    ) -> List[GatewayPositionModel]:
        """
        Get open positions from Binance.

        Args:
            **kwargs: Keyword arguments for positions retrieval. Common arguments include:
                - symbol: Trading symbol (e.g., "BTCUSDT") to filter positions.
                If not provided, returns all open positions.

        Returns:
            List of GatewayPositionModel instances containing position information.
            Returns empty list if no positions are found or an error occurs.
        """
        return self._position_component.get_positions(**kwargs)

    def get_verification(
        self,
        **kwargs: Any,
    ) -> Dict[str, bool]:
        """
        Get account verification status from Binance.

        Args:
            **kwargs: Keyword arguments for verification retrieval. Typically empty,
                but may include additional parameters.

        Returns:
            Dictionary containing verification status information with boolean values.
            Common keys include 'futures_enabled', 'deposit_enabled', 'withdraw_enabled'.
        """
        return self._account_component.get_verification(**kwargs)

    # ───────────────────────────────────────────────────────────
    # PRIVATE METHODS
    # ───────────────────────────────────────────────────────────
    def _build_urls(
        self,
        sandbox: bool,
    ) -> Dict[str, str]:
        """
        Build Binance API URLs based on sandbox mode.

        Args:
            sandbox: Whether to use sandbox/testnet endpoints.

        Returns:
            Dictionary containing fapi_url, fapi_v2_url, and fapi_ws_url.
        """
        if sandbox:
            return {
                "fapi_url": "https://testnet.binancefuture.com/fapi/v1",
                "fapi_v2_url": "https://testnet.binancefuture.com/fapi/v2",
                "fapi_ws_url": "wss://stream.binancefuture.com/ws",
            }

        return {
            "fapi_url": "https://fapi.binance.com/fapi/v1",
            "fapi_v2_url": "https://fapi.binance.com/fapi/v2",
            "fapi_ws_url": "wss://fstream.binance.com/ws",
        }
