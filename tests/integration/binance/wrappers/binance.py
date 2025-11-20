# Code reviewed on 2025-11-20 by Pedro Carvajal

import datetime
import time
import unittest
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from configs.timezone import TIMEZONE
from enums.order_side import OrderSide
from enums.order_status import OrderStatus
from enums.order_type import OrderType
from helpers.get_env import get_env
from models.order import OrderModel
from services.gateway import GatewayService
from services.gateway.models.enums.gateway_order_status import GatewayOrderStatus
from services.gateway.models.gateway_kline import GatewayKlineModel
from services.gateway.models.gateway_order import GatewayOrderModel
from services.gateway.models.gateway_position import GatewayPositionModel
from services.logging import LoggingService

if TYPE_CHECKING:
    from services.strategy.handlers.gateway import GatewayHandler


class BinanceWrapper(unittest.TestCase):
    """
    Base test wrapper class for Binance integration tests.

    Provides common setup and helper methods for testing Binance gateway
    functionality. Handles test order creation, position management, and
    order cleanup operations.

    Attributes:
        _SYMBOL: Default trading symbol for tests (BTCUSDT).
        _DEFAULT_ORDER_VOLUME: Default order volume for test orders.
        _gateway: GatewayService instance for Binance operations.
        _log: LoggingService instance for test logging.
        _verification: Account verification status dictionary.
    """

    # ───────────────────────────────────────────────────────────
    # CONSTANTS
    # ───────────────────────────────────────────────────────────
    _SYMBOL: str = "BTCUSDT"
    _DEFAULT_ORDER_VOLUME: float = 0.002

    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    _gateway: GatewayService
    _log: LoggingService
    _verification: Optional[Dict[str, bool]]

    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def setUp(self) -> None:
        """Initialize test wrapper with gateway service and logging.

        Sets up the Binance gateway service in sandbox mode, initializes
        logging, and verifies that credentials are properly configured.
        This method is called automatically by unittest before each test.

        Raises:
            AssertionError: If sandbox mode is not enabled, verification
                fails, or credentials are not configured.
        """
        self._log = LoggingService()
        self._log.setup(name=self.__class__.__name__)

        self._validate_sandbox_configuration()

        self._gateway = GatewayService(
            gateway="binance",
        )

        self._verification = self._gateway.get_verification()

        assert self._gateway.sandbox is True, "Sandbox must be enabled for tests"
        assert self._verification is not None, "Verification should not be None"
        assert self._verification["credentials_configured"] is True, "Credentials should be configured"

    # ───────────────────────────────────────────────────────────
    # ORDER MANAGEMENT
    # ───────────────────────────────────────────────────────────
    def _place_test_order(
        self,
        symbol: Optional[str] = None,
        side: OrderSide = OrderSide.BUY,
        volume: Optional[float] = None,
        price: Optional[float] = None,
    ) -> Optional[GatewayOrderModel]:
        """Place a test order through the gateway.

        Places an order with the specified parameters. If symbol or volume
        are not provided, uses default values. If price is provided, creates
        a LIMIT order; otherwise creates a MARKET order.

        Args:
            symbol: Trading symbol (e.g., "BTCUSDT"). Defaults to _SYMBOL
                if not provided.
            side: Order side (BUY or SELL). Defaults to BUY.
            volume: Order volume. Defaults to _DEFAULT_ORDER_VOLUME if
                not provided.
            price: Order price. If provided, creates a LIMIT order. If None,
                creates a MARKET order.

        Returns:
            GatewayOrderModel instance if order placement succeeds, None
            if order placement fails.
        """
        if symbol is None:
            symbol = self._SYMBOL

        if volume is None:
            volume = self._DEFAULT_ORDER_VOLUME

        order_type = OrderType.MARKET if price is None else OrderType.LIMIT

        return self._gateway.place_order(
            symbol=symbol,
            side=side,
            order_type=order_type,
            volume=volume,
            price=price,
        )

    def _build_order_model(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        volume: float,
        price: float = 0.0,
        backtest: bool = False,
    ) -> OrderModel:
        """Build an OrderModel instance for testing.

        Args:
            symbol: Trading symbol (e.g., "BTCUSDT").
            side: Order side (BUY or SELL).
            order_type: Order type (MARKET, LIMIT, etc.).
            volume: Order volume.
            price: Order price (default: 0.0).
            backtest: Whether order is for backtest mode (default: False).

        Returns:
            OrderModel instance configured with provided parameters.
        """
        return OrderModel(
            symbol=symbol,
            side=side,
            order_type=order_type,
            volume=volume,
            price=price,
            backtest=backtest,
            gateway=self._gateway,
            created_at=datetime.datetime.now(tz=TIMEZONE),
            updated_at=datetime.datetime.now(tz=TIMEZONE),
        )

    def _delete_order_by_id(
        self,
        symbol: str,
        order_id: str,
    ) -> None:
        """Delete/cleanup an order by its ID.

        Retrieves the order from the gateway and handles cleanup based on
        the order status:
        - PENDING orders are cancelled
        - EXECUTED orders have their positions closed
        - Other statuses are logged as already closed/cancelled

        Args:
            symbol: Trading symbol for the order.
            order_id: Unique identifier of the order to delete/cleanup.
        """
        order = self._gateway.get_order(
            symbol=symbol,
            order_id=order_id,
        )

        if not order:
            self._log.warning(f"Order {order_id} not found")
            return

        if order.status == GatewayOrderStatus.PENDING:
            self._cancel_order(
                symbol=symbol,
                order=order,
                order_id=order_id,
            )

        elif order.status == GatewayOrderStatus.EXECUTED:
            self._close_position_for_order(
                symbol=symbol,
                order=order,
                order_id=order_id,
            )

        else:
            self._log.info(f"Order {order_id} is already closed or cancelled")

    def _close_position(
        self,
        symbol: str,
        order: GatewayOrderModel,
    ) -> None:
        """Close a position opened by the given order.

        Retrieves positions for the symbol and closes the first position
        found. If no position exists or the position volume is zero,
        logs a warning and returns without action.

        Args:
            symbol: Trading symbol for the position.
            order: The order that opened the position to close.
        """
        positions = self._gateway.get_positions(symbol=symbol)

        if len(positions) == 0:
            self._log.warning(f"No position found for order {order.id}")
            return

        position = positions[0]

        if position.volume == 0:
            self._log.info(f"No position to close for order {order.id}")
            return

        close_side, close_volume = self._compute_close_parameters(
            order=order,
            position=position,
        )

        self._place_close_order(
            symbol=symbol,
            order=order,
            close_side=close_side,
            close_volume=close_volume,
        )

    def _cancel_order(
        self,
        symbol: str,
        order: GatewayOrderModel,
        order_id: str,
    ) -> None:
        """Cancel a pending order.

        Attempts to cancel the specified pending order through the gateway.
        Logs success or raises an assertion error if cancellation fails.

        Args:
            symbol: Trading symbol for the order.
            order: The GatewayOrderModel instance to cancel.
            order_id: Unique identifier of the order (for logging).

        Raises:
            AssertionError: If the order cancellation fails.
        """
        cancelled_order = self._gateway.cancel_order(
            symbol=symbol,
            order=order,
        )

        assert cancelled_order is not None, f"Failed to cancel order {order_id}"
        self._log.info(f"Order {order_id} cancelled successfully")

    # ───────────────────────────────────────────────────────────
    # VALIDATION (Assert operations)
    # ───────────────────────────────────────────────────────────
    def _assert_order_is_valid(
        self,
        order: Optional[GatewayOrderModel],
        expected_type: OrderType,
        expected_symbol: Optional[str] = None,
    ) -> None:
        """Assert that an order is valid.

        Validates that an order meets all expected criteria including type,
        symbol, volume, and status.

        Args:
            order: The order to validate.
            expected_type: The expected order type (MARKET, LIMIT, etc.).
            expected_symbol: The expected trading symbol. If None, uses
                _SYMBOL constant.

        Raises:
            AssertionError: If the order does not meet validation criteria.
        """
        if expected_symbol is None:
            expected_symbol = self._SYMBOL

        assert order is not None, "Order should not be None"
        assert isinstance(order, GatewayOrderModel), "Order should be a GatewayOrderModel"
        assert order.id != "", "Order ID should not be empty"
        assert order.symbol == expected_symbol, f"Symbol should be {expected_symbol}"
        assert order.order_type == expected_type, f"Order type should be {expected_type}"
        assert order.volume > 0, "Volume should be > 0"
        assert order.executed_volume >= 0, "Executed volume should be >= 0"

        if expected_type.is_market():
            assert order.status in [
                GatewayOrderStatus.PENDING,
                GatewayOrderStatus.EXECUTED,
            ], "Status should be PENDING or EXECUTED"

        assert order.response is not None, "Response should not be None"

    def _assert_order_is_cancelled(
        self,
        cancelled_order: Optional[GatewayOrderModel],
        original_order: GatewayOrderModel,
    ) -> None:
        """Assert that an order is cancelled.

        Validates that a cancelled order matches the original order ID and
        has the CANCELLED status.

        Args:
            cancelled_order: The cancelled order to validate.
            original_order: The original order that was cancelled.

        Raises:
            AssertionError: If the order cancellation validation fails.
        """
        assert cancelled_order is not None, "Cancelled order should not be None"
        assert isinstance(cancelled_order, GatewayOrderModel), "Cancelled order should be a GatewayOrderModel"
        assert cancelled_order.id == original_order.id, "Cancelled order ID should match original order ID"
        assert cancelled_order.status == GatewayOrderStatus.CANCELLED, "Order status should be CANCELLED"
        assert cancelled_order.response is not None, "Response should not be None"

    # ───────────────────────────────────────────────────────────
    # DATA RETRIEVAL
    # ───────────────────────────────────────────────────────────
    def _fetch_latest_candle(
        self,
        symbol: str,
        timeframe: str = "1m",
        lookback_minutes: int = 5,
    ) -> GatewayKlineModel:
        """Fetch the latest candle/kline.

        Retrieves the most recent candle for the specified symbol and
        timeframe within the lookback period.

        Args:
            symbol: Trading symbol (e.g., "BTCUSDT").
            timeframe: Timeframe for the candle (e.g., "1m", "5m", "1h").
                Defaults to "1m".
            lookback_minutes: Number of minutes to look back for candles.
                Defaults to 5 minutes.

        Returns:
            GatewayKlineModel instance representing the latest candle.

        Raises:
            AssertionError: If no candle is found or close price is invalid.
        """
        latest_kline: Optional[GatewayKlineModel] = None

        def callback(klines: List[GatewayKlineModel]) -> None:
            nonlocal latest_kline

            if klines:
                latest_kline = klines[-1]

        end_time = datetime.datetime.now(tz=TIMEZONE)
        start_time = end_time - datetime.timedelta(minutes=lookback_minutes)

        self._gateway.get_klines(
            symbol=symbol,
            timeframe=timeframe,
            from_date=start_time.timestamp(),
            to_date=end_time.timestamp(),
            callback=callback,
        )

        assert latest_kline is not None, "Latest kline should not be None"
        assert latest_kline.close_price > 0, "Close price should be > 0"

        return latest_kline

    def _get_limit_price(
        self,
        symbol: str,
        discount: float = 0.9,
        lookback_minutes: int = 5,
    ) -> float:
        """Get calculated limit price.

        Calculates a limit price based on the current market price with
        a discount factor, rounded to the symbol's tick size and precision.

        Args:
            symbol: Trading symbol (e.g., "BTCUSDT").
            discount: Discount factor to apply to current price (0.0-1.0).
                Defaults to 0.9 (10% discount).
            lookback_minutes: Number of minutes to look back for price data.
                Defaults to 5 minutes.

        Returns:
            Calculated limit price rounded to symbol's precision.

        Raises:
            AssertionError: If symbol info is invalid or tick size is missing.
        """
        symbol_info = self._gateway.get_symbol_info(symbol=symbol)

        assert symbol_info is not None, "Symbol info should not be None"
        assert symbol_info.tick_size is not None, "Tick size should not be None"

        latest_kline = self._fetch_latest_candle(
            symbol=symbol,
            timeframe="1m",
            lookback_minutes=lookback_minutes,
        )

        current_price = latest_kline.close_price
        limit_price_raw = current_price * discount
        tick_size = symbol_info.tick_size
        limit_price_rounded = round(limit_price_raw / tick_size) * tick_size
        limit_price = round(limit_price_rounded, symbol_info.price_precision)

        discount_percent = int(discount * 100)

        self._log.info(f"Current price: {current_price}, Limit price ({discount_percent}%): {limit_price}")

        return limit_price

    # ───────────────────────────────────────────────────────────
    # POLLING/WAITING (Async operations)
    # ───────────────────────────────────────────────────────────
    def _wait_for_order_status(
        self,
        order: "OrderModel",
        target_status: OrderStatus,
        timeout_seconds: int = 70,
        handler: Optional["GatewayHandler"] = None,
    ) -> None:
        """Wait for order to reach target status (polling operation).

        Polls the order status until it reaches the target status or the
        timeout is reached. Checks both the order status directly and the
        polling task completion status if a handler is provided.

        Args:
            order: OrderModel instance to wait for.
            target_status: Target OrderStatus to wait for.
            timeout_seconds: Maximum time to wait in seconds. Defaults to 70.
            handler: Optional GatewayHandler instance to check polling tasks.
                If provided, also checks handler's polling task status.

        Raises:
            TimeoutError: If order does not reach target status within
                timeout_seconds.
        """
        self._log.info(f"Waiting for order {order.id} to reach {target_status} (max {timeout_seconds}s)")

        start_time = time.time()
        polling_tasks = {}

        if handler:
            polling_tasks = getattr(handler, "_polling_tasks", {})

        while time.time() - start_time < timeout_seconds:
            if order.status == target_status:
                elapsed = time.time() - start_time
                self._log.info(f"Order reached {target_status} after {elapsed:.1f}s")
                return

            if handler and order.id in polling_tasks:
                task = polling_tasks[order.id]
                if task.done():
                    self._log.info("Polling task completed")
                    return

            time.sleep(1)

        raise TimeoutError(
            f"Order {order.id} did not reach {target_status} within {timeout_seconds} seconds",
        )

    # ───────────────────────────────────────────────────────────
    # PRIVATE METHODS (Internal computations)
    # ───────────────────────────────────────────────────────────
    def _validate_sandbox_configuration(self) -> None:
        """Validate sandbox mode and credentials configuration before creating gateway.

        Checks that:
        - BINANCE_TESTNET environment variable is set to enable sandbox mode
        - BINANCE_TESTNET_API_KEY is configured
        - BINANCE_TESTNET_API_SECRET is configured

        Raises:
            AssertionError: If sandbox mode is not enabled or credentials are missing.
        """
        sandbox_env = get_env("BINANCE_TESTNET", default="True")
        sandbox_enabled = sandbox_env.lower() in ("true", "1", "yes", "on") if sandbox_env else True

        assert sandbox_enabled is True, (
            "BINANCE_TESTNET must be enabled for tests. Set BINANCE_TESTNET=True in environment variables"
        )

        testnet_api_key = get_env("BINANCE_TESTNET_API_KEY")
        testnet_api_secret = get_env("BINANCE_TESTNET_API_SECRET")

        assert testnet_api_key is not None, (
            "BINANCE_TESTNET_API_KEY must be configured for tests. Set BINANCE_TESTNET_API_KEY in environment variables"
        )

        assert testnet_api_key != "", (
            "BINANCE_TESTNET_API_KEY must not be empty. Set BINANCE_TESTNET_API_KEY in environment variables"
        )

        assert testnet_api_secret is not None, (
            "BINANCE_TESTNET_API_SECRET must be configured for tests. "
            "Set BINANCE_TESTNET_API_SECRET in environment variables"
        )
        assert testnet_api_secret != "", (
            "BINANCE_TESTNET_API_SECRET must not be empty. Set BINANCE_TESTNET_API_SECRET in environment variables"
        )

    def _compute_close_parameters(
        self,
        order: GatewayOrderModel,
        position: GatewayPositionModel,
    ) -> Tuple[OrderSide, float]:
        """Compute close side and volume parameters.

        Args:
            order: The order that opened the position.
            position: The position to close.

        Returns:
            Tuple containing:
                - OrderSide: The side to use for the close order (opposite of open order).
                - float: The absolute volume of the position to close.
        """
        close_side = OrderSide.SELL if order.side and order.side.is_buy() else OrderSide.BUY
        close_volume = abs(position.volume)

        return close_side, close_volume

    def _place_close_order(
        self,
        symbol: str,
        order: GatewayOrderModel,
        close_side: OrderSide,
        close_volume: float,
    ) -> None:
        """Place an order to close a position.

        Args:
            symbol: Trading symbol for the close order.
            order: The original order that opened the position.
            close_side: The side to use for the close order.
            close_volume: The volume to close.

        Raises:
            AssertionError: If the close order placement fails.
        """
        close_order = self._gateway.place_order(
            symbol=symbol,
            side=close_side,
            order_type=OrderType.MARKET,
            volume=close_volume,
        )

        assert close_order is not None, f"Failed to close position for order {order.id}"
        self._log.info(f"Position closed for order {order.id}")

    def _close_position_for_order(
        self,
        symbol: str,
        order: GatewayOrderModel,
        order_id: str,
    ) -> None:
        """Close position for an executed order.

        Retrieves positions for the symbol and closes the position opened
        by the executed order. Asserts that a position exists and has
        non-zero volume before attempting to close.

        Args:
            symbol: Trading symbol for the position.
            order: The executed order that opened the position.
            order_id: Unique identifier of the order (for error messages).

        Raises:
            AssertionError: If no position is found or position volume is zero.
        """
        positions = self._gateway.get_positions(symbol=symbol)

        assert len(positions) > 0, f"No position found for order {order_id}"

        position = positions[0]

        assert position.volume != 0, f"No position to close for order {order_id}"

        close_side, close_volume = self._compute_close_parameters(
            order=order,
            position=position,
        )

        self._place_close_order(
            symbol=symbol,
            order=order,
            close_side=close_side,
            close_volume=close_volume,
        )
