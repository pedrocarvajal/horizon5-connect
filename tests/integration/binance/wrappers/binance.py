# Code reviewed on 2025-11-21 by Pedro Carvajal

import unittest
from typing import Dict, Optional, Tuple

from enums.order_side import OrderSide
from enums.order_type import OrderType
from helpers.get_env import get_env
from services.gateway import GatewayService
from services.gateway.models.enums.gateway_order_status import GatewayOrderStatus
from services.gateway.models.gateway_order import GatewayOrderModel
from services.gateway.models.gateway_position import GatewayPositionModel
from services.logging import LoggingService


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
