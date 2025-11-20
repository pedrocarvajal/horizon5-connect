# Code reviewed on 2025-11-20 by Pedro Carvajal

import asyncio
import datetime
from typing import Any, Dict, Optional

from configs.timezone import TIMEZONE
from enums.order_status import OrderStatus
from models.order import OrderModel
from services.gateway import GatewayService
from services.gateway.models.enums.gateway_order_status import GatewayOrderStatus
from services.gateway.models.gateway_order import GatewayOrderModel
from services.logging import LoggingService


class GatewayHandler:
    """
    Handler for gateway operations and configuration validation.

    This handler manages gateway service interactions, validates gateway
    configuration for production trading, and executes real orders on the
    exchange when in production mode. It provides a base class for gateway
    operations that can be extended by specific handlers.

    The handler performs:
    - Gateway configuration validation (credentials, leverage, balance, etc.)
    - Trading requirements verification (margin mode, position mode, permissions)
    - Real order execution on exchange gateways (production mode only)

    Attributes:
        _gateway: Gateway service instance for trading operations.
        _log: Logging service instance for logging operations.
        _backtest: Whether running in backtest mode.
        _backtest_id: Optional backtest identifier.
        _verification: Dictionary containing gateway verification status.
        _polling_tasks: Dictionary mapping order IDs to async polling tasks.
    """

    # ───────────────────────────────────────────────────────────
    # CONSTANTS
    # ───────────────────────────────────────────────────────────
    MAX_POLLING_RETRIES: int = 5
    MAX_POLLING_ITERATIONS: int = 60
    POLLING_INTERVAL_SECONDS: int = 1

    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    _gateway: GatewayService
    _log: LoggingService
    _backtest: bool
    _backtest_id: Optional[str]
    _verification: Optional[Dict[str, bool]]
    _polling_tasks: Dict[str, asyncio.Task]

    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(
        self,
        gateway: GatewayService,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the gateway handler.

        Args:
            gateway: Gateway service instance for trading operations.
            **kwargs: Additional keyword arguments:
                backtest: Whether running in backtest mode (default: False).
                backtest_id: Optional backtest identifier.

        Raises:
            ValueError: If gateway configuration is invalid for production trading.
        """
        self._log = LoggingService()
        self._log.setup("gateway_handler")

        self._gateway = gateway

        self._backtest = kwargs.get("backtest", False)
        self._backtest_id = kwargs.get("backtest_id")
        self._verification = None
        self._polling_tasks = {}

        if not self._backtest:
            self._verification = self._gateway.get_verification()
            self._validate_gateway_configuration()

    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def open_order(self, order: OrderModel) -> bool:
        """
        Execute a real order on the exchange gateway.

        Places an order on the exchange when in production mode. In backtest mode,
        this method returns False without executing. Updates the OrderModel with
        gateway order information upon successful placement.

        Args:
            order: OrderModel instance containing order details to execute.

        Returns:
            True if the order was placed successfully, False otherwise.
        """
        if order.backtest:
            return False

        gateway_order = self._gateway.place_order(
            symbol=order.symbol,
            side=order.side,
            order_type=order.order_type,
            volume=order.volume,
            price=order.price if order.price > 0 else None,
            client_order_id=order.client_order_id,
        )

        if gateway_order is None:
            self._log.error(f"Failed to place order {order.id} on gateway")
            return False

        order.gateway_order_id = gateway_order.id

        if gateway_order.price > 0:
            order.price = gateway_order.price

        order.executed_volume = gateway_order.executed_volume
        order.status = self._map_gateway_status_to_order_status(gateway_order.status)
        self._pull_order_status(order)

        return True

    # ───────────────────────────────────────────────────────────
    # PRIVATE METHODS
    # ───────────────────────────────────────────────────────────
    def _validate_gateway_configuration(self) -> None:
        """
        Validate gateway configuration for production trading.

        Checks if API credentials are configured. If not configured, logs
        warnings and returns early. If configured, proceeds to check trading
        requirements.

        This method is only called when not in backtest mode.
        """
        if self._verification is None:
            return

        credentials_configured = self._verification.get("credentials_configured", False)

        if not credentials_configured:
            self._log.warning("API credentials not configured in gateway config")
            self._log.warning("Operating in backtest mode without live trading capabilities")
            return

        self._check_trading_requirements()

    def _check_trading_requirements(self) -> None:
        """
        Check all trading requirements for production trading.

        Validates that the gateway configuration meets all requirements:
        - API credentials are configured
        - Leverage is set to 1x or higher
        - USDT balance is available
        - Account is in cross margin mode
        - Account is in one-way position mode
        - Trading permissions are enabled

        Raises:
            ValueError: If any trading requirement is not met.
        """
        if self._verification is None:
            return

        credentials_configured = self._verification.get("credentials_configured", False)
        required_leverage = self._verification.get("required_leverage", False)
        usdt_balance = self._verification.get("usdt_balance", False)
        cross_margin = self._verification.get("cross_margin", False)
        one_way_mode = self._verification.get("one_way_mode", False)
        trading_permissions = self._verification.get("trading_permissions", False)

        if not credentials_configured:
            raise ValueError("API credentials not configured in gateway config")

        if not required_leverage:
            raise ValueError("Leverage must be set to 1x or higher for the trading symbol")

        if not usdt_balance:
            raise ValueError("USDT balance is zero - deposit funds to enable trading")

        if not cross_margin:
            raise ValueError("Account must be configured in cross margin mode")

        if not one_way_mode:
            raise ValueError("Account must be in one-way position mode (disable hedge mode)")

        if not trading_permissions:
            raise ValueError("Trading permissions disabled - check API key restrictions or account status")

        self._log.success("Gateway configuration validated successfully")
        self._log.success(f"Running sandbox: {self._gateway.sandbox}")

    def _get_gateway_status_map(self) -> Dict[GatewayOrderStatus, OrderStatus]:
        """
        Get the mapping dictionary from GatewayOrderStatus to OrderStatus.

        Returns:
            Dictionary mapping gateway order statuses to internal order statuses.
        """
        return {
            GatewayOrderStatus.PENDING: OrderStatus.OPENING,
            GatewayOrderStatus.EXECUTED: OrderStatus.OPEN,
            GatewayOrderStatus.CANCELLED: OrderStatus.CANCELLED,
        }

    def _map_gateway_status_to_order_status(
        self,
        gateway_status: Optional[GatewayOrderStatus],
    ) -> OrderStatus:
        """
        Map GatewayOrderStatus to OrderStatus.

        Converts gateway-specific order status to internal order status:
        - PENDING → OPENING
        - EXECUTED → OPEN
        - CANCELLED → CANCELLED

        Args:
            gateway_status: Gateway order status to map.

        Returns:
            OrderStatus: Mapped order status. Defaults to OPENING if status is None
                or unrecognized.
        """
        if gateway_status is None:
            return OrderStatus.OPENING

        return self._get_gateway_status_map().get(gateway_status, OrderStatus.OPENING)

    def _pull_order_status(self, order: OrderModel) -> None:
        """
        Start asynchronous polling task to verify order status.

        Creates an async task that polls the gateway for order status updates
        until the order reaches a final state (EXECUTED or CANCELLED).

        Args:
            order: OrderModel instance to poll status for.
        """
        if order.backtest or not order.gateway_order_id:
            return

        self._create_polling_task(order)

    def _create_polling_task(self, order: OrderModel) -> None:
        """
        Create and register an async polling task for order status.

        Handles both running and non-running event loops, creating appropriate
        async tasks or running synchronously when needed.

        Args:
            order: OrderModel instance to poll status for.
        """
        try:
            loop = asyncio.get_event_loop()

            if loop.is_running():
                task = asyncio.create_task(self._get_order_status_from_gateway(order))
                self._polling_tasks[order.id] = task
            else:
                loop.run_until_complete(self._get_order_status_from_gateway(order))

        except RuntimeError:
            task = asyncio.create_task(self._get_order_status_from_gateway(order))
            self._polling_tasks[order.id] = task

    async def _get_order_status_from_gateway(self, order: OrderModel) -> None:
        """
        Poll gateway for order status until it reaches a final state.

        Continuously checks the order status on the gateway at configured intervals
        until the order is EXECUTED or CANCELLED. Updates the OrderModel with
        final execution data including trades and commissions.

        Args:
            order: OrderModel instance to poll status for.
        """
        if order.backtest or not order.gateway_order_id:
            return

        retry_count = 0
        iteration_count = 0

        while iteration_count < self.MAX_POLLING_ITERATIONS:
            await asyncio.sleep(self.POLLING_INTERVAL_SECONDS)
            iteration_count += 1

            gateway_order = self._gateway.get_order(
                symbol=order.symbol,
                order_id=order.gateway_order_id,
            )

            if gateway_order is None:
                retry_count += 1

                if retry_count >= self.MAX_POLLING_RETRIES:
                    self._log.warning(
                        f"Order {order.id} not found after {self.MAX_POLLING_RETRIES} attempts, stopping polling",
                    )
                    return

                continue

            retry_count = 0

            if not self._should_continue_polling(gateway_order.status):
                if gateway_order.status == GatewayOrderStatus.EXECUTED:
                    self._handle_executed_order(order, gateway_order)
                elif gateway_order.status == GatewayOrderStatus.CANCELLED:
                    self._handle_cancelled_order(order)

                return

        self._log.warning(
            f"Order {order.id} polling stopped after {self.MAX_POLLING_ITERATIONS} iterations without final status",
        )

    def _should_continue_polling(self, status: Optional[GatewayOrderStatus]) -> bool:
        """
        Check if polling should continue based on order status.

        Args:
            status: Current gateway order status.

        Returns:
            bool: True if polling should continue, False if order reached final state.
        """
        return status == GatewayOrderStatus.PENDING

    def _handle_executed_order(
        self,
        order: OrderModel,
        gateway_order: GatewayOrderModel,
    ) -> None:
        """
        Handle order execution completion.

        Updates the order with execution data and final execution details.

        Args:
            order: OrderModel instance to update.
            gateway_order: Gateway order model with execution details.
        """
        gateway_trades = self._gateway.get_trades(
            symbol=order.symbol,
            order_id=order.gateway_order_id,
        )

        if gateway_trades:
            order.trades = gateway_trades

        order.executed_volume = gateway_order.executed_volume
        order.price = gateway_order.price
        order.status = OrderStatus.OPEN
        order.updated_at = datetime.datetime.now(tz=TIMEZONE)

        self._log.success(f"Order {order.id} executed successfully")

    def _handle_cancelled_order(self, order: OrderModel) -> None:
        """
        Handle order cancellation.

        Updates the order status to CANCELLED and logs the cancellation.

        Args:
            order: OrderModel instance to update.
        """
        order.status = OrderStatus.CANCELLED
        order.updated_at = datetime.datetime.now(tz=TIMEZONE)

        self._log.error(f"Order {order.id} was cancelled")
