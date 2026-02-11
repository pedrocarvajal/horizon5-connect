"""Gateway handler service for production order execution."""

import asyncio
import datetime
import re
import threading
from typing import Any, Dict, List, Optional

from vendor.configs.timezone import TIMEZONE
from vendor.enums.order_side import OrderSide
from vendor.enums.order_status import OrderStatus
from vendor.enums.order_type import OrderType
from vendor.interfaces.gateway import GatewayInterface
from vendor.interfaces.gateway_handler import GatewayHandlerInterface
from vendor.interfaces.logging import LoggingInterface
from vendor.models.order import OrderModel
from vendor.services.gateway.models.enums.gateway_order_status import GatewayOrderStatus
from vendor.services.gateway.models.gateway_order import GatewayOrderModel
from vendor.services.gateway.models.gateway_symbol_info import GatewaySymbolInfoModel
from vendor.services.logging import LoggingService
from vendor.services.orderbook.models import OrderSyncResult


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
        _backtest_id: Optional backtest identifier.
        _verification: Dictionary containing gateway verification status.
        _polling_tasks: Dictionary mapping order IDs to async polling tasks.
    """

    MAX_POLLING_ITERATIONS: int = 60
    MAX_POLLING_RETRIES: int = 5
    MAX_SYMBOL_LENGTH: int = 20
    POLLING_INTERVAL_SECONDS: int = 1
    SYMBOL_PATTERN: str = r"^[A-Z0-9]+$"

    _backtest_id: Optional[str]
    _cache_lock: threading.Lock
    _polling_lock: threading.Lock
    _polling_tasks: Dict[str, asyncio.Task[None]]
    _symbol_info_cache: Dict[str, GatewaySymbolInfoModel]
    _verification: Optional[Dict[str, bool]]

    _log: LoggingInterface

    def __init__(
        self,
        gateway: GatewayInterface,
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

        self._gateway = gateway

        self._backtest_id = kwargs.get("backtest_id")
        self._verification = None
        self._polling_tasks = {}
        self._polling_lock = threading.Lock()
        self._symbol_info_cache = {}
        self._cache_lock = threading.Lock()

        if not self.backtest:
            self._verification = self._gateway.get_verification()
            self._validate_gateway_configuration()

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
            self._log.error(
                "Order has no gateway_order_id to cancel",
                order_id=order.id,
            )
            return False

        if not (order.status.is_opening() or order.status.is_open()):
            self._log.error(
                "Order cannot be cancelled",
                order_id=order.id,
                status=order.status.value,
                reason="Only OPENING or OPEN orders can be cancelled",
            )
            return False

        try:
            gateway_order = self._gateway.cancel_order(
                symbol=order.symbol,
                order_id=order.gateway_order_id,
            )
        except Exception as e:
            self._log.error(
                "Exception cancelling order",
                order_id=order.id,
                error=str(e),
            )
            return False

        if gateway_order is None:
            self._log.error(
                "Failed to cancel order on gateway",
                order_id=order.id,
            )
            return False

        if gateway_order.executed_volume > 0 and gateway_order.executed_volume != order.executed_volume:
            order.executed_volume = gateway_order.executed_volume
            self._log.warning(
                "Order had partial fills before cancellation",
                order_id=order.id,
                filled=f"{gateway_order.executed_volume}/{order.volume}",
            )

        with self._polling_lock:
            if order.id in self._polling_tasks:
                task = self._polling_tasks.pop(order.id)

                if not task.done():
                    task.cancel()

                self._log.info(
                    "Stopped polling task for cancelled order",
                    order_id=order.id,
                )

        order.status = OrderStatus.CANCELLED
        order.updated_at = datetime.datetime.now(tz=TIMEZONE)

        self._log.info(
            "Order cancelled successfully",
            order_id=order.id,
        )

        return True

    def close_position(self, order: OrderModel) -> bool:
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
            self._log.error(
                "Order has invalid symbol for close operation",
                order_id=order.id,
            )
            return False

        if order.side is None:
            self._log.error(
                "Order has no side defined",
                order_id=order.id,
            )
            return False

        if order.executed_volume <= 0:
            self._log.error(
                "Order has no executed volume to close",
                order_id=order.id,
                executed_volume=order.executed_volume,
            )
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
            self._log.error(
                "Exception closing order",
                order_id=order.id,
                error=str(e),
            )
            return False

        if gateway_order is None:
            self._log.error(
                "Failed to close order on gateway",
                order_id=order.id,
            )
            return False

        order.gateway_order_id = gateway_order.id

        if gateway_order.price > 0:
            order.close_price = gateway_order.price

        order.status = OrderStatus.CLOSING
        order.updated_at = datetime.datetime.now(tz=TIMEZONE)
        self._pull_order_status(order)

        return True

    def place_order(self, order: OrderModel) -> bool:
        """
        Place an order on the exchange gateway.

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
            self._log.error(
                "Exception placing order",
                order_id=order.id,
                error=str(e),
            )
            return False

        if gateway_order is None:
            self._log.error(
                "Failed to place order on gateway",
                order_id=order.id,
            )
            return False

        order.gateway_order_id = gateway_order.id

        if gateway_order.price > 0:
            order.price = gateway_order.price

        order.executed_volume = gateway_order.executed_volume
        order.status = self._map_gateway_status_to_order_status(gateway_order.status)
        self._pull_order_status(order)

        return True

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
            self._log.warning(
                "Polling task was cancelled",
                order_id=order_id,
            )
        elif task.exception() is not None:
            self._log.error(
                "Polling task raised exception",
                order_id=order_id,
                error=str(task.exception()),
            )

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
                self._log.error(
                    "Exception polling order",
                    order_id=order.id,
                    error=str(e),
                )
                retry_count += 1

                if retry_count >= self.MAX_POLLING_RETRIES:
                    self._log.error(
                        "Order polling failed after max retries",
                        order_id=order.id,
                        max_retries=self.MAX_POLLING_RETRIES,
                    )
                    order.status = OrderStatus.CANCELLED
                    order.updated_at = datetime.datetime.now(tz=TIMEZONE)
                    return

                continue

            if gateway_order is None:
                self._log.info(
                    "Order not in pending orders, searching in positions",
                    order_id=order.id,
                    attempt=retry_count + 1,
                )

                gateway_order = self._find_order_in_positions(order)

                if gateway_order is None:
                    retry_count += 1

                    if retry_count >= self.MAX_POLLING_RETRIES:
                        self._log.error(
                            "Order not found in orders or positions after max attempts",
                            order_id=order.id,
                            max_attempts=self.MAX_POLLING_RETRIES,
                        )

                        order.status = OrderStatus.CANCELLED
                        order.updated_at = datetime.datetime.now(tz=TIMEZONE)

                        return

                    continue

                self._log.info(
                    "Order found in positions",
                    order_id=order.id,
                    position_id=gateway_order.id,
                )

            retry_count = 0

            if not self._should_continue_polling(gateway_order.status):
                try:
                    if gateway_order.status == GatewayOrderStatus.EXECUTED:
                        self._handle_executed_order(order, gateway_order)
                    elif gateway_order.status == GatewayOrderStatus.CANCELLED:
                        self._handle_cancelled_order(order)
                except Exception as e:
                    self._log.error(
                        "Failed to finalize order",
                        order_id=order.id,
                        status=str(gateway_order.status),
                        error=str(e),
                    )
                    order.status = OrderStatus.CANCELLED
                    order.updated_at = datetime.datetime.now(tz=TIMEZONE)

                return

        self._log.warning(
            "Order polling stopped without final status",
            order_id=order.id,
            max_iterations=self.MAX_POLLING_ITERATIONS,
        )
        order.status = OrderStatus.CANCELLED
        order.updated_at = datetime.datetime.now(tz=TIMEZONE)

    def _find_order_in_positions(
        self,
        order: OrderModel,
    ) -> Optional[GatewayOrderModel]:
        """
        Search for an executed order in open positions.

        When gateways execute MARKET orders immediately, the order may not
        exist in pending orders but as an open position. This method searches
        positions to find an order that was already executed.

        Matching is done by:
        - Position ID matching gateway_order_id
        - Position clientId matching client_order_id

        Args:
            order: OrderModel to search for in positions.

        Returns:
            GatewayOrderModel with EXECUTED status if found, None otherwise.
        """
        try:
            positions = self._gateway.get_positions(symbol=order.symbol)
        except Exception as e:
            self._log.warning(
                "Failed to get positions for order lookup",
                order_id=order.id,
                error=str(e),
            )
            return None

        for position in positions:
            if not position.response:
                continue

            position_id = str(position.response.get("id", ""))
            position_client_id = position.response.get("clientId", "")
            id_match = position_id == order.gateway_order_id
            client_id_match = position_client_id and position_client_id == order.client_order_id

            if id_match or client_id_match:
                return GatewayOrderModel(
                    id=position_id,
                    symbol=position.symbol,
                    side=position.side,
                    order_type=OrderType.MARKET,
                    status=GatewayOrderStatus.EXECUTED,
                    volume=abs(position.volume),
                    executed_volume=abs(position.volume),
                    price=position.open_price,
                    response=position.response,
                )

        return None

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
            self._log.warning(
                "Failed to get symbol info",
                symbol=symbol,
                error=str(e),
            )
            return None

    def _handle_cancelled_order(self, order: OrderModel) -> None:
        """
        Handle order cancellation.

        Updates the order status to CANCELLED and logs the cancellation.

        Args:
            order: OrderModel instance to update.
        """
        order.status = OrderStatus.CANCELLED
        order.updated_at = datetime.datetime.now(tz=TIMEZONE)

        self._log.error(
            "Order was cancelled",
            order_id=order.id,
        )

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
            self._log.error(
                "Exception retrieving trades for order",
                order_id=order.id,
                error=str(e),
            )

        order.executed_volume = gateway_order.executed_volume

        if order.status == OrderStatus.CLOSING:
            order.close_price = gateway_order.price
            order.status = OrderStatus.CLOSED
            self._log.success(
                "Order closed successfully",
                order_id=order.id,
            )
        else:
            order.price = gateway_order.price
            order.status = OrderStatus.OPEN
            self._log.success(
                "Order executed successfully",
                order_id=order.id,
            )

        order.updated_at = datetime.datetime.now(tz=TIMEZONE)

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

    def _should_continue_polling(self, status: Optional[GatewayOrderStatus]) -> bool:
        """
        Check if polling should continue based on order status.

        Args:
            status: Current gateway order status.

        Returns:
            bool: True if polling should continue, False if order reached final state.
        """
        return status == GatewayOrderStatus.PENDING

    def _validate_basic_parameters(self, order: OrderModel) -> bool:
        """
        Validate basic order parameters.

        Args:
            order: OrderModel instance to validate.

        Returns:
            True if basic parameters are valid, False otherwise.
        """
        if not order.symbol or order.symbol.strip() == "":
            self._log.error(
                "Order has invalid symbol",
                order_id=order.id,
            )
            return False

        symbol = order.symbol.strip().upper()
        if symbol != order.symbol:
            self._log.error(
                "Order symbol must be uppercase without whitespace",
                order_id=order.id,
            )
            return False

        if len(order.symbol) > self.MAX_SYMBOL_LENGTH:
            self._log.error(
                "Order symbol too long",
                order_id=order.id,
                length=len(order.symbol),
            )
            return False

        if not re.match(self.SYMBOL_PATTERN, order.symbol):
            self._log.error(
                "Order symbol contains invalid characters",
                order_id=order.id,
            )
            return False

        if order.side is None:
            self._log.error(
                "Order has invalid or missing side",
                order_id=order.id,
            )
            return False

        if order.order_type is None:
            self._log.error(
                "Order has invalid or missing order type",
                order_id=order.id,
            )
            return False

        if order.volume <= 0:
            self._log.error(
                "Order has invalid volume",
                order_id=order.id,
                volume=order.volume,
            )
            return False

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
            self._log.warning(
                "Could not retrieve symbol info, skipping range validation",
                symbol=order.symbol,
            )
            return True

        return self._validate_symbol_info_constraints(order, symbol_info)

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
            self._log.error(
                "Order price below minimum",
                order_id=order.id,
                price=order.price,
                min_price=symbol_info.min_price,
            )
            return False

        if symbol_info.max_price is not None and order.price > symbol_info.max_price:
            self._log.error(
                "Order price exceeds maximum",
                order_id=order.id,
                price=order.price,
                max_price=symbol_info.max_price,
            )
            return False

        notional_value = order.volume * order.price

        if symbol_info.min_notional is not None and notional_value < symbol_info.min_notional:
            self._log.error(
                "Order notional value below minimum",
                order_id=order.id,
                notional_value=notional_value,
                min_notional=symbol_info.min_notional,
            )
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
            self._log.error(
                "Order volume below minimum",
                order_id=order.id,
                volume=order.volume,
                min_quantity=symbol_info.min_quantity,
            )
            return False

        if symbol_info.max_quantity is not None and order.volume > symbol_info.max_quantity:
            self._log.error(
                "Order volume exceeds maximum",
                order_id=order.id,
                volume=order.volume,
                max_quantity=symbol_info.max_quantity,
            )
            return False

        return not (order.price > 0 and not self._validate_price_constraints(order, symbol_info))

    def sync_orders(
        self,
        open_orders: Dict[str, OrderModel],
    ) -> Dict[str, OrderSyncResult]:
        """
        Sync multiple orders with gateway positions (batch operation).

        Queries gateway for all positions and compares with local open orders.
        Returns update results for orders that have changed state.

        Args:
            open_orders: Dictionary of order_id -> OrderModel for orders that
                        should be open according to local state.

        Returns:
            Dictionary mapping order_id to OrderSyncResult for orders
            that were closed externally. Empty dict if no changes or backtest.
        """
        if self.backtest or not open_orders:
            return {}

        gateway_positions = self._fetch_gateway_positions()

        if gateway_positions is None:
            return {}

        gateway_position_map = self._build_position_map(gateway_positions)
        results: Dict[str, OrderSyncResult] = {}

        for order_id, order in open_orders.items():
            if not order.gateway_order_id:
                continue

            position_exists = self._order_exists_in_gateway(order, gateway_position_map)

            if not position_exists:
                result = self._fetch_close_info(order)
                results[order_id] = result

                self._log.warning(
                    "Order closed externally (manual intervention detected)",
                    order_id=order.id,
                    gateway_order_id=order.gateway_order_id,
                    close_price=result.close_price,
                    profit=result.profit,
                )

        return results

    def update_order(self, order: OrderModel) -> OrderSyncResult:
        """
        Update a single order's state from gateway.

        Checks if the order still exists in gateway positions. If not,
        fetches close information from trade history.

        Args:
            order: OrderModel to update from gateway.

        Returns:
            OrderSyncResult with current state from gateway.
        """
        if self.backtest:
            return OrderSyncResult(
                exists=True,
                status=order.status,
                executed_volume=order.executed_volume,
                current_price=order.close_price,
            )

        if not order.gateway_order_id:
            return OrderSyncResult(
                exists=False,
                status=OrderStatus.CANCELLED,
            )

        gateway_positions = self._fetch_gateway_positions()

        if gateway_positions is None:
            return OrderSyncResult(
                exists=True,
                status=order.status,
                executed_volume=order.executed_volume,
                current_price=order.close_price,
            )

        gateway_position_map = self._build_position_map(gateway_positions)
        position_exists = self._order_exists_in_gateway(order, gateway_position_map)

        if position_exists:
            position = gateway_position_map.get(order.gateway_order_id)
            current_price = position.open_price if position else order.close_price

            return OrderSyncResult(
                exists=True,
                status=OrderStatus.OPEN,
                executed_volume=order.executed_volume,
                current_price=current_price,
            )

        return self._fetch_close_info(order)

    def _fetch_gateway_positions(self) -> Optional[List[Any]]:
        """
        Fetch all positions from gateway.

        Returns:
            List of gateway positions or None if fetch failed.
        """
        try:
            return self._gateway.get_positions()
        except Exception as e:
            self._log.error(
                "Failed to fetch gateway positions",
                error=str(e),
            )
            return None

    def _build_position_map(
        self,
        positions: List[Any],
    ) -> Dict[str, Any]:
        """
        Build a map of position IDs to position objects.

        Args:
            positions: List of gateway position objects.

        Returns:
            Dictionary mapping position/client IDs to position objects.
        """
        position_map: Dict[str, Any] = {}

        for position in positions:
            if not position.response:
                continue

            position_id = str(position.response.get("id", ""))
            client_id = str(position.response.get("clientId", ""))

            if position_id:
                position_map[position_id] = position

            if client_id:
                position_map[client_id] = position

        return position_map

    def _order_exists_in_gateway(
        self,
        order: OrderModel,
        position_map: Dict[str, Any],
    ) -> bool:
        """
        Check if an order exists in the gateway position map.

        Args:
            order: Order to check.
            position_map: Map of position IDs to positions.

        Returns:
            True if order exists in gateway, False otherwise.
        """
        return order.gateway_order_id in position_map or bool(
            order.client_order_id and order.client_order_id in position_map
        )

    def _fetch_close_info(self, order: OrderModel) -> OrderSyncResult:
        """
        Fetch close information for a closed order from trade history.

        Args:
            order: The order to get close info for.

        Returns:
            OrderSyncResult with close price and profit from exchange.
        """
        close_price = order.close_price if order.close_price > 0 else order.price
        profit = 0.0

        try:
            trades = self._gateway.get_trades(
                symbol=order.symbol,
                position_id=order.gateway_order_id,
            )

            if trades:
                close_trade = trades[-1]

                if close_trade.price > 0:
                    close_price = close_trade.price

                if order.side and order.side.is_buy():
                    profit = (close_price - order.price) * order.executed_volume
                else:
                    profit = (order.price - close_price) * order.executed_volume

        except Exception as e:
            self._log.warning(
                "Failed to fetch trade history for closed order",
                order_id=order.id,
                error=str(e),
            )

            if order.side and order.side.is_buy():
                profit = (close_price - order.price) * order.executed_volume
            else:
                profit = (order.price - close_price) * order.executed_volume

        return OrderSyncResult(
            exists=False,
            status=OrderStatus.CLOSED,
            close_price=close_price,
            profit=profit,
            executed_volume=order.executed_volume,
        )
