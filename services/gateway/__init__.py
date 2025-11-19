# Code reviewed on 2025-11-19 by pedrocarvajal

from typing import Any, Dict, List, Optional

from configs.gateways import GATEWAYS
from interfaces.gateway import GatewayInterface
from services.gateway.models.gateway_account import GatewayAccountModel
from services.gateway.models.gateway_leverage_info import GatewayLeverageInfoModel
from services.gateway.models.gateway_order import GatewayOrderModel
from services.gateway.models.gateway_position import GatewayPositionModel
from services.gateway.models.gateway_symbol_info import GatewaySymbolInfoModel
from services.gateway.models.gateway_trade import GatewayTradeModel
from services.gateway.models.gateway_trading_fees import GatewayTradingFeesModel
from services.logging import LoggingService


class GatewayService(GatewayInterface):
    """
    Service for managing gateway operations.

    This service acts as a facade/wrapper for gateway implementations,
    providing a unified interface to interact with different trading
    gateways (e.g., Binance). It handles gateway initialization,
    configuration, and delegates all operations to the underlying
    gateway implementation.

    Attributes:
        _name: Name of the gateway to use (e.g., "binance").
        _sandbox: Whether to use sandbox/testnet mode.
        _gateways: Dictionary containing gateway configurations.
        _gateway: Instance of the underlying gateway implementation.
        _log: Logging service instance for logging operations.
    """

    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    _name: str
    _sandbox: bool
    _gateways: Dict[str, Any]

    _gateway: GatewayInterface
    _log: LoggingService

    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(
        self,
        gateway: str,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the gateway service.

        Args:
            gateway: Name of the gateway to use (e.g., "binance").
                Must be a key in the GATEWAYS configuration.
            **kwargs: Additional keyword arguments. Supported keys:
                - sandbox: Whether to use sandbox/testnet mode (default: False).

        Raises:
            ValueError: If the specified gateway name is not found in
                the GATEWAYS configuration.
        """
        self._log = LoggingService()
        self._log.setup(name="gateway_service")

        self._gateways = GATEWAYS
        self._name = gateway
        self._sandbox = kwargs.get("sandbox", False)

        self._setup()

    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def get_klines(
        self,
        **kwargs: Any,
    ) -> None:
        """
        Get klines (candlestick data) from the gateway.

        This method delegates to the underlying gateway implementation.
        The actual behavior depends on the gateway's implementation.

        Args:
            **kwargs: Keyword arguments passed to the gateway's get_klines method.
                Common arguments include symbol, interval, start_time, end_time, limit.
        """
        self._gateway.get_klines(**kwargs)

    def get_symbol_info(
        self,
        **kwargs: Any,
    ) -> Optional[GatewaySymbolInfoModel]:
        """
        Get symbol information from the gateway.

        Args:
            **kwargs: Keyword arguments passed to the gateway's get_symbol_info method.
                Typically includes 'symbol' parameter.

        Returns:
            GatewaySymbolInfoModel instance containing symbol information,
            or None if the symbol is not found or an error occurs.
        """
        return self._gateway.get_symbol_info(**kwargs)

    def get_trading_fees(
        self,
        **kwargs: Any,
    ) -> Optional[GatewayTradingFeesModel]:
        """
        Get trading fees information from the gateway.

        Args:
            **kwargs: Keyword arguments passed to the gateway's get_trading_fees method.
                Typically includes 'symbol' parameter.

        Returns:
            GatewayTradingFeesModel instance containing trading fees information,
            or None if the information cannot be retrieved or an error occurs.
        """
        return self._gateway.get_trading_fees(**kwargs)

    def get_leverage_info(
        self,
        **kwargs: Any,
    ) -> Optional[GatewayLeverageInfoModel]:
        """
        Get leverage information from the gateway.

        Args:
            **kwargs: Keyword arguments passed to the gateway's get_leverage_info method.
                Typically includes 'symbol' parameter.

        Returns:
            GatewayLeverageInfoModel instance containing leverage information,
            or None if the information cannot be retrieved or an error occurs.
        """
        return self._gateway.get_leverage_info(**kwargs)

    def get_order(
        self,
        **kwargs: Any,
    ) -> Optional[GatewayOrderModel]:
        """
        Get order information from the gateway.

        Args:
            **kwargs: Keyword arguments passed to the gateway's get_order method.
                Typically includes 'symbol' and 'order_id' or 'client_order_id' parameters.

        Returns:
            GatewayOrderModel instance containing order information,
            or None if the order is not found or an error occurs.
        """
        return self._gateway.get_order(**kwargs)

    async def stream(
        self,
        **kwargs: Any,
    ) -> None:
        """
        Stream real-time data from the gateway.

        This is an async method that establishes a WebSocket connection
        to stream market data, order updates, or other real-time information.

        Args:
            **kwargs: Keyword arguments passed to the gateway's stream method.
                Common arguments include symbols, streams, callbacks.

        Note:
            This method should be awaited and will run until the stream
            is closed or an error occurs.
        """
        await self._gateway.stream(**kwargs)

    def place_order(
        self,
        **kwargs: Any,
    ) -> Optional[GatewayOrderModel]:
        """
        Place a new order on the gateway.

        Args:
            **kwargs: Keyword arguments passed to the gateway's place_order method.
                Common arguments include:
                - symbol: Trading symbol (e.g., "BTCUSDT")
                - side: Order side (BUY or SELL)
                - order_type: Order type (MARKET, LIMIT, etc.)
                - volume: Order volume/quantity
                - price: Order price (required for LIMIT orders)
                - client_order_id: Optional client-side order identifier

        Returns:
            GatewayOrderModel instance containing the placed order information,
            or None if the order placement fails or an error occurs.
        """
        return self._gateway.place_order(**kwargs)

    def cancel_order(
        self,
        **kwargs: Any,
    ) -> Optional[GatewayOrderModel]:
        """
        Cancel an existing order on the gateway.

        Args:
            **kwargs: Keyword arguments passed to the gateway's cancel_order method.
                Common arguments include:
                - symbol: Trading symbol (e.g., "BTCUSDT")
                - order_id: Gateway order ID
                - client_order_id: Client-side order identifier

        Returns:
            GatewayOrderModel instance containing the cancelled order information,
            or None if the cancellation fails or an error occurs.
        """
        return self._gateway.cancel_order(**kwargs)

    def modify_order(
        self,
        **kwargs: Any,
    ) -> Optional[GatewayOrderModel]:
        """
        Modify an existing order on the gateway.

        Args:
            **kwargs: Keyword arguments passed to the gateway's modify_order method.
                Common arguments include:
                - symbol: Trading symbol (e.g., "BTCUSDT")
                - order_id: Gateway order ID
                - client_order_id: Client-side order identifier
                - price: New order price
                - volume: New order volume/quantity

        Returns:
            GatewayOrderModel instance containing the modified order information,
            or None if the modification fails or an error occurs.
        """
        return self._gateway.modify_order(**kwargs)

    def set_leverage(
        self,
        **kwargs: Any,
    ) -> bool:
        """
        Set leverage for a symbol on the gateway.

        Args:
            **kwargs: Keyword arguments passed to the gateway's set_leverage method.
                Common arguments include:
                - symbol: Trading symbol (e.g., "BTCUSDT")
                - leverage: Leverage value to set

        Returns:
            True if leverage was set successfully, False otherwise.
        """
        return self._gateway.set_leverage(**kwargs)

    def get_account(
        self,
        **kwargs: Any,
    ) -> Optional[GatewayAccountModel]:
        """
        Get account information from the gateway.

        Args:
            **kwargs: Keyword arguments passed to the gateway's get_account method.
                Typically no arguments are required, but gateway-specific
                parameters may be supported.

        Returns:
            GatewayAccountModel instance containing account information
            (balance, positions, etc.), or None if the information cannot
            be retrieved or an error occurs.
        """
        return self._gateway.get_account(
            **kwargs,
        )

    def get_verification(
        self,
        **kwargs: Any,
    ) -> Dict[str, bool]:
        """
        Get verification status from the gateway.

        This method checks API credentials validity, account configuration,
        and trading requirements.

        Args:
            **kwargs: Keyword arguments passed to the gateway's get_verification method.
                Common arguments include:
                - symbol: Trading symbol to check leverage for (default: "BTCUSDT").

        Returns:
            Dictionary containing verification status information with boolean values.
            Keys include 'credentials_configured', 'required_leverage', 'usdt_balance',
            'cross_margin', 'one_way_mode', and 'trading_permissions'.
        """
        return self._gateway.get_verification(**kwargs)

    def get_orders(
        self,
        **kwargs: Any,
    ) -> List[GatewayOrderModel]:
        """
        Get multiple orders from the gateway.

        Args:
            **kwargs: Keyword arguments passed to the gateway's get_orders method.
                Common arguments include:
                - symbol: Trading symbol to filter orders (e.g., "BTCUSDT")
                - start_time: Start timestamp for order filtering
                - end_time: End timestamp for order filtering
                - limit: Maximum number of orders to return

        Returns:
            List of GatewayOrderModel instances containing order information.
            Returns an empty list if no orders are found or an error occurs.
        """
        return self._gateway.get_orders(**kwargs)

    def get_trades(
        self,
        **kwargs: Any,
    ) -> List[GatewayTradeModel]:
        """
        Get trade history from the gateway.

        Args:
            **kwargs: Keyword arguments passed to the gateway's get_trades method.
                Common arguments include:
                - symbol: Trading symbol to filter trades (e.g., "BTCUSDT")
                - start_time: Start timestamp for trade filtering
                - end_time: End timestamp for trade filtering
                - limit: Maximum number of trades to return

        Returns:
            List of GatewayTradeModel instances containing trade information.
            Returns an empty list if no trades are found or an error occurs.
        """
        return self._gateway.get_trades(**kwargs)

    def get_positions(
        self,
        **kwargs: Any,
    ) -> List[GatewayPositionModel]:
        """
        Get open positions from the gateway.

        Args:
            **kwargs: Keyword arguments passed to the gateway's get_positions method.
                Common arguments include:
                - symbol: Trading symbol to filter positions (e.g., "BTCUSDT").
                    If not provided, returns all positions.

        Returns:
            List of GatewayPositionModel instances containing position information.
            Returns an empty list if no positions are open or an error occurs.
        """
        return self._gateway.get_positions(**kwargs)

    # ───────────────────────────────────────────────────────────
    # PRIVATE METHODS
    # ───────────────────────────────────────────────────────────
    def _setup(self) -> None:
        """
        Set up the gateway instance.

        Validates the gateway name, prepares configuration, and instantiates
        the underlying gateway implementation. This method is called during
        initialization and should not be called directly.

        Raises:
            ValueError: If the specified gateway name is not found in
                the GATEWAYS configuration.
        """
        if self._name not in self._gateways:
            raise ValueError(f"Gateway {self._name} not found")

        self._log.info(f"Setting up gateway {self._name}")

        gateway_config = self._gateways[self._name]
        gateway_kwargs = gateway_config["kwargs"].copy()

        if self._sandbox:
            gateway_kwargs["sandbox"] = True

        self._gateway = gateway_config["class"](**gateway_kwargs)

    # ───────────────────────────────────────────────────────────
    # GETTERS
    # ───────────────────────────────────────────────────────────
    @property
    def name(self) -> str:
        """
        Get the gateway name.

        Returns:
            Name of the gateway being used (e.g., "binance").
        """
        return self._name

    @property
    def sandbox(self) -> bool:
        """
        Get the sandbox mode.

        Returns:
            True if the gateway is in sandbox mode, False otherwise.
        """
        return self._sandbox
