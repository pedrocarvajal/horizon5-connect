"""Gateway handler service for production order execution."""

import asyncio
import datetime
import re
import threading
from typing import Any, Dict, Optional

from configs.timezone import TIMEZONE
from enums.order_side import OrderSide
from enums.order_status import OrderStatus
from enums.order_type import OrderType
from interfaces.gateway_handler import GatewayHandlerInterface
from models.order import OrderModel
from services.gateway import GatewayService
from services.gateway.models.enums.gateway_order_status import GatewayOrderStatus
from services.gateway.models.gateway_order import GatewayOrderModel
from services.gateway.models.gateway_symbol_info import GatewaySymbolInfoModel
from services.logging import LoggingService


class GatewayHandlerService(GatewayHandlerInterface):
    """
    Service for gateway operations and configuration validation.

    This service manages gateway interactions, validates gateway
    configuration for production trading, and executes real orders on the
    exchange when in production mode.

    The service performs:
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

    MAX_POLLING_RETRIES: int = 5
    MAX_POLLING_ITERATIONS: int = 60
    POLLING_INTERVAL_SECONDS: int = 1
    MAX_SYMBOL_LENGTH: int = 20
    SYMBOL_PATTERN: str = r"^[A-Z0-9]+$"

    _gateway: GatewayService
    _log: LoggingService
    _backtest: bool
    _backtest_id: Optional[str]
    _verification: Optional[Dict[str, bool]]
    _polling_tasks: Dict[str, asyncio.Task[None]]
    _polling_lock: threading.Lock
    _symbol_info_cache: Dict[str, GatewaySymbolInfoModel]
    _cache_lock: threading.Lock

    def __init__(
        self,
        gateway: GatewayService,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the gateway handler service.

        Args:
            gateway: Gateway service instance for trading operations.
            **kwargs: Additional keyword arguments:
                backtest: Whether running in backtest mode (default: False).
                backtest_id: Optional backtest identifier.

        Raises:
            ValueError: If gateway configuration is invalid for production trading.
        """
        self._log = LoggingService()
        self._log.setup("gateway_handler_service")

        self._gateway = gateway

        self._backtest = kwargs.get("backtest", False)
        self._backtest_id = kwargs.get("backtest_id")
        self._verification = None
        self._polling_tasks = {}
        self._polling_lock = threading.Lock()
        self._symbol_info_cache = {}
        self._cache_lock = threading.Lock()

        if not self._backtest:
            self._verification = self._gateway.get_verification()
            self._validate_gateway_configuration()

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

        if not self._validate_order_parameters(order):
            return False

        try:
            gateway_order = self._gateway.place_order(
                symbol=order.symbol,
                side=order.side,
                order_type=order.order_type,
                volume=order.volume,
                price=order.price if order.price > 0 else None,
                client_order_id=order.client_order_id,
            )
        except Exception as e:
            self._log.error(f"Exception placing order {order.id}: {e}")
            return False

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

    def _validate_order_parameters(self, order: OrderModel) -> bool:
        """
        Validate order parameters before sending to gateway.

        Performs comprehensive validation including:
        - Basic parameter checks (symbol, side, type, volume)
        - Symbol format validation
        - Volume range validation (min/max from gateway symbol info)
        - Price range validation (min/max from gateway symbol info)
        - Notional value validation (min order value)
        - Safety checks for fat-finger errors

        Args:
            order: OrderModel instance to validate.

        Returns:
            True if order parameters are valid, False otherwise.
        """
        if not self._validate_basic_parameters(order):
            return False

        symbol_info = self._get_symbol_info(order.symbol)

        if symbol_info is None:
            self._log.warning(f"Could not retrieve symbol info for {order.symbol}, skipping range validation")
            return True

        return self._validate_symbol_info_constraints(order, symbol_info)

    def _validate_basic_parameters(self, order: OrderModel) -> bool:
        """
        Validate basic order parameters.

        Args:
            order: OrderModel instance to validate.

        Returns:
            True if basic parameters are valid, False otherwise.
        """
        if not order.symbol or order.symbol.strip() == "":
            self._log.error(f"Order {order.id} has invalid symbol")
            return False

        symbol = order.symbol.strip().upper()
        if symbol != order.symbol:
            self._log.error(f"Order {order.id} symbol must be uppercase without whitespace")
            return False

        if len(order.symbol) > self.MAX_SYMBOL_LENGTH:
            self._log.error(f"Order {order.id} symbol too long: {len(order.symbol)} chars")
            return False

        if not re.match(self.SYMBOL_PATTERN, order.symbol):
            self._log.error(f"Order {order.id} symbol contains invalid characters")
            return False

        if order.side is None:
            self._log.error(f"Order {order.id} has invalid or missing side")
            return False

        if order.order_type is None:
            self._log.error(f"Order {order.id} has invalid or missing order type")
            return False

        if order.volume <= 0:
            self._log.error(f"Order {order.id} has invalid volume: {order.volume}")
            return False

        return True

    def _validate_symbol_info_constraints(
        self,
        order: OrderModel,
        symbol_info: GatewaySymbolInfoModel,
    ) -> bool:
        """
        Validate order against symbol info constraints.

        Args:
            order: OrderModel instance to validate.
            symbol_info: Symbol info containing trading constraints.

        Returns:
            True if order meets symbol constraints, False otherwise.
        """
        if symbol_info.min_quantity is not None and order.volume < symbol_info.min_quantity:
            self._log.error(f"Order {order.id} volume {order.volume} below minimum {symbol_info.min_quantity}")
            return False

        if symbol_info.max_quantity is not None and order.volume > symbol_info.max_quantity:
            self._log.error(f"Order {order.id} volume {order.volume} exceeds maximum {symbol_info.max_quantity}")
            return False

        return not (order.price > 0 and not self._validate_price_constraints(order, symbol_info))

    def _validate_price_constraints(
        self,
        order: OrderModel,
        symbol_info: GatewaySymbolInfoModel,
    ) -> bool:
        """
        Validate order price against symbol constraints.

        Args:
            order: OrderModel instance to validate.
            symbol_info: Symbol info containing price constraints.

        Returns:
            True if price meets constraints, False otherwise.
        """
        if symbol_info.min_price is not None and order.price < symbol_info.min_price:
            self._log.error(f"Order {order.id} price {order.price} below minimum {symbol_info.min_price}")
            return False

        if symbol_info.max_price is not None and order.price > symbol_info.max_price:
            self._log.error(f"Order {order.id} price {order.price} exceeds maximum {symbol_info.max_price}")
            return False

        notional_value = order.volume * order.price

        if symbol_info.min_notional is not None and notional_value < symbol_info.min_notional:
            self._log.error(
                f"Order {order.id} notional value {notional_value} below minimum {symbol_info.min_notional}"
            )
            return False

        return True

    def _get_symbol_info(self, symbol: str) -> Optional[GatewaySymbolInfoModel]:
        """
        Get symbol information from gateway with caching.

        Args:
            symbol: Trading symbol to get info for.

        Returns:
            GatewaySymbolInfoModel if available, None otherwise.
        """
        with self._cache_lock:
            if symbol in self._symbol_info_cache:
                return self._symbol_info_cache[symbol]

        try:
            symbol_info = self._gateway.get_symbol_info(symbol=symbol)
            if symbol_info is not None:
                with self._cache_lock:
                    self._symbol_info_cache[symbol] = symbol_info
            return symbol_info
        except Exception as e:
            self._log.warning(f"Failed to get symbol info for {symbol}: {e}")
            return None

    def close_order(self, order: OrderModel) -> bool:
        """
        Close an open position by placing an opposite order on the exchange gateway.

        Closes a position by placing a market order in the opposite direction with
        the same volume. In backtest mode, returns False without executing.
        Updates the order with closing information and polls for execution status.

        Args:
            order: OrderModel instance representing the position to close.

        Returns:
            True if the closing order was placed successfully, False otherwise.
        """
        if order.backtest:
            return False

        if not order.symbol or order.symbol.strip() == "":
            self._log.error(f"Order {order.id} has invalid symbol for close operation")
            return False

        if order.side is None:
            self._log.error(f"Order {order.id} has no side defined")
            return False

        if order.executed_volume <= 0:
            self._log.error(f"Order {order.id} has no executed volume to close: {order.executed_volume}")
            return False

        close_side = OrderSide.SELL if order.side.is_buy() else OrderSide.BUY

        try:
            gateway_order = self._gateway.place_order(
                symbol=order.symbol,
                side=close_side,
                order_type=OrderType.MARKET,
                volume=order.executed_volume,
            )
        except Exception as e:
            self._log.error(f"Exception closing order {order.id}: {e}")
            return False

        if gateway_order is None:
            self._log.error(f"Failed to close order {order.id} on gateway")
            return False

        order.gateway_order_id = gateway_order.id

        if gateway_order.price > 0:
            order.close_price = gateway_order.price

        order.status = OrderStatus.CLOSING
        order.updated_at = datetime.datetime.now(tz=TIMEZONE)
        self._pull_order_status(order)

        return True

    def cancel_order(self, order: OrderModel) -> bool:
        """
        Cancel a pending order on the exchange gateway.

        Cancels an order that is still pending execution (OPENING state).
        In backtest mode, returns False without executing. Stops any active
        polling tasks for the order and updates the order status to CANCELLED.

        Args:
            order: OrderModel instance representing the order to cancel.

        Returns:
            True if the order was cancelled successfully, False otherwise.
        """
        if order.backtest:
            return False

        if not order.gateway_order_id:
            self._log.error(f"Order {order.id} has no gateway_order_id to cancel")
            return False

        if not (order.status.is_opening() or order.status.is_open()):
            msg = f"Order {order.id} cannot be cancelled in status {order.status.value}."
            self._log.error(f"{msg} Only OPENING or OPEN orders can be cancelled.")
            return False

        try:
            gateway_order = self._gateway.cancel_order(
                symbol=order.symbol,
                order_id=order.gateway_order_id,
            )
        except Exception as e:
            self._log.error(f"Exception cancelling order {order.id}: {e}")
            return False

        if gateway_order is None:
            self._log.error(f"Failed to cancel order {order.id} on gateway")
            return False

        if gateway_order.executed_volume > 0 and gateway_order.executed_volume != order.executed_volume:
            order.executed_volume = gateway_order.executed_volume
            filled = f"{gateway_order.executed_volume}/{order.volume}"
            self._log.warning(f"Order {order.id} had partial fills before cancellation: {filled}")

        with self._polling_lock:
            if order.id in self._polling_tasks:
                task = self._polling_tasks.pop(order.id)

                if not task.done():
                    task.cancel()

                self._log.info(f"Stopped polling task for cancelled order {order.id}")

        order.status = OrderStatus.CANCELLED
        order.updated_at = datetime.datetime.now(tz=TIMEZONE)

        self._log.info(f"Order {order.id} cancelled successfully")

        return True

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
            loop = asyncio.get_running_loop()
            task = asyncio.create_task(self._get_order_status_from_gateway(order))
            task.add_done_callback(lambda t: self._cleanup_polling_task(order.id, t))

            with self._polling_lock:
                self._polling_tasks[order.id] = task

        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                loop.run_until_complete(self._get_order_status_from_gateway(order))
            finally:
                loop.close()
                asyncio.set_event_loop(None)

    def _cleanup_polling_task(
        self,
        order_id: str,
        task: asyncio.Task[None],
    ) -> None:
        """
        Clean up completed polling task and handle any exceptions.

        Args:
            order_id: ID of the order whose task completed.
            task: The completed async task.
        """
        with self._polling_lock:
            if order_id in self._polling_tasks:
                del self._polling_tasks[order_id]

        if task.cancelled():
            self._log.warning(f"Polling task for order {order_id} was cancelled")
        elif task.exception() is not None:
            self._log.error(f"Polling task for order {order_id} raised exception: {task.exception()}")

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

            try:
                gateway_order = self._gateway.get_order(
                    symbol=order.symbol,
                    order_id=order.gateway_order_id,
                )
            except Exception as e:
                self._log.error(f"Exception polling order {order.id}: {e}")
                retry_count += 1

                if retry_count >= self.MAX_POLLING_RETRIES:
                    self._log.error(
                        f"Order {order.id} polling failed after {self.MAX_POLLING_RETRIES} exceptions",
                    )
                    order.status = OrderStatus.CANCELLED
                    order.updated_at = datetime.datetime.now(tz=TIMEZONE)
                    return

                continue

            if gateway_order is None:
                retry_count += 1

                if retry_count >= self.MAX_POLLING_RETRIES:
                    self._log.warning(
                        f"Order {order.id} not found after {self.MAX_POLLING_RETRIES} attempts, stopping polling",
                    )
                    order.status = OrderStatus.CANCELLED
                    order.updated_at = datetime.datetime.now(tz=TIMEZONE)
                    return

                continue

            retry_count = 0

            if not self._should_continue_polling(gateway_order.status):
                try:
                    if gateway_order.status == GatewayOrderStatus.EXECUTED:
                        self._handle_executed_order(order, gateway_order)
                    elif gateway_order.status == GatewayOrderStatus.CANCELLED:
                        self._handle_cancelled_order(order)
                except Exception as e:
                    self._log.error(f"Failed to finalize order {order.id} with status {gateway_order.status}: {e}")
                    order.status = OrderStatus.CANCELLED
                    order.updated_at = datetime.datetime.now(tz=TIMEZONE)

                return

        self._log.warning(
            f"Order {order.id} polling stopped after {self.MAX_POLLING_ITERATIONS} iterations without final status",
        )
        order.status = OrderStatus.CANCELLED
        order.updated_at = datetime.datetime.now(tz=TIMEZONE)

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
        Sets status to OPEN for opening orders or CLOSED for closing orders.

        Args:
            order: OrderModel instance to update.
            gateway_order: Gateway order model with execution details.
        """
        try:
            gateway_trades = self._gateway.get_trades(
                symbol=order.symbol,
                order_id=order.gateway_order_id,
            )

            if gateway_trades:
                order.trades = gateway_trades
        except Exception as e:
            self._log.error(f"Exception retrieving trades for order {order.id}: {e}")

        order.executed_volume = gateway_order.executed_volume

        if order.status == OrderStatus.CLOSING:
            order.close_price = gateway_order.price
            order.status = OrderStatus.CLOSED
            self._log.success(f"Order {order.id} closed successfully")
        else:
            order.price = gateway_order.price
            order.status = OrderStatus.OPEN
            self._log.success(f"Order {order.id} executed successfully")

        order.updated_at = datetime.datetime.now(tz=TIMEZONE)

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
