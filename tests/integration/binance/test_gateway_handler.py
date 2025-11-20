# Code reviewed on 2025-11-20 by Pedro Carvajal

import time
from typing import TYPE_CHECKING

from enums.order_side import OrderSide
from enums.order_status import OrderStatus
from enums.order_type import OrderType
from services.strategy.handlers.gateway import GatewayHandler
from tests.integration.binance.wrappers.binance import BinanceWrapper

if TYPE_CHECKING:
    from models.order import OrderModel


class TestGatewayHandler(BinanceWrapper):
    # ───────────────────────────────────────────────────────────
    # CONSTANTS
    # ───────────────────────────────────────────────────────────
    _SYMBOL: str = "BTCUSDT"
    _DEFAULT_VOLUME: float = 0.002
    _POLLING_TIMEOUT_SECONDS: int = 70
    _DEFAULT_ORDER_BACKTEST_ID: str = "test-123"
    _DEFAULT_ORDER_INVALID_SYMBOL: str = "INVALID_SYMBOL"
    _DEFAULT_ORDER_INVALID_VOLUME: float = 0.0

    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    _handler: GatewayHandler

    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def setUp(self) -> None:
        super().setUp()
        self._log.setup(name="test_gateway_handler")

        self._handler = GatewayHandler(
            gateway=self._gateway,
            backtest=False,
        )

    def test_gateway_handler_initialization(self) -> None:
        self._log.info("Testing GatewayHandler initialization")

        assert self._handler is not None, "Handler should be initialized"
        assert self._handler._gateway is not None, "Handler should have gateway"
        assert self._handler._backtest is False, "Handler should not be in backtest mode"

        self._log.info("GatewayHandler initialized successfully")

    def test_open_order_market_with_polling(self) -> None:
        self._log.info("Testing open_order with market order and polling")

        order = self._create_test_order(
            symbol=self._SYMBOL,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            volume=self._DEFAULT_VOLUME,
        )

        result = self._handler.open_order(order)

        assert result is True, "open_order should return True for production mode"
        assert order.gateway_order_id is not None, "Order should have gateway_order_id"
        assert order.gateway_order_id != "", "Gateway order ID should not be empty"
        valid_statuses = [OrderStatus.OPENING, OrderStatus.OPEN]
        status_message = f"Order status should be OPENING or OPEN, got {order.status}"
        assert order.status in valid_statuses, status_message

        self._log.info(f"Order placed successfully: {order.gateway_order_id}")

        self._wait_for_order_execution(order)

        assert order.status == OrderStatus.OPEN, f"Order should be OPEN after polling, got {order.status}"
        assert order.executed_volume > 0, "Order should have executed volume"
        assert order.price >= 0, "Order should have execution price (>= 0)"
        assert order.updated_at is not None, "Order should have updated_at timestamp"

        if order.price == 0:
            self._log.warning("Order price is 0, attempting to get from gateway")

            gateway_order = self._gateway.get_order(
                symbol=self._SYMBOL,
                order_id=order.gateway_order_id,
            )

            if gateway_order and gateway_order.price > 0:
                self._log.info(f"Retrieved price from gateway: {gateway_order.price}")
            else:
                self._log.warning("Gateway order also has price 0")

        if order.trades:
            self._log.info(f"Order has {len(order.trades)} trades")

            for trade in order.trades:
                assert trade.price > 0, "Trade price should be > 0"
                assert trade.volume > 0, "Trade volume should be > 0"

        trades_count = len(order.trades) if order.trades else 0
        log_msg = f"Order executed: price={order.price}, volume={order.executed_volume}, "
        log_msg += f"trades={trades_count}"
        self._log.info(log_msg)

        self._close_order_by_id(symbol=self._SYMBOL, order_id=order.gateway_order_id)

    def test_open_order_backtest_mode(self) -> None:
        self._log.info("Testing open_order in backtest mode")

        handler_backtest = GatewayHandler(
            gateway=self._gateway,
            backtest=True,
            backtest_id=self._DEFAULT_ORDER_BACKTEST_ID,
        )

        order = self._create_test_order(
            symbol=self._SYMBOL,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            volume=self._DEFAULT_VOLUME,
            backtest=True,
        )

        result = handler_backtest.open_order(order)

        expected_result = False
        message = "open_order should return False in backtest mode"

        assert result is expected_result, message
        assert order.gateway_order_id is None, "Order should not have gateway_order_id"

        self._log.info("Backtest mode correctly prevented order placement")

    def test_open_order_with_invalid_gateway_response(self) -> None:
        self._log.info("Testing open_order with invalid parameters")

        order = self._create_test_order(
            symbol=self._DEFAULT_ORDER_INVALID_SYMBOL,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            volume=self._DEFAULT_ORDER_INVALID_VOLUME,
        )

        result = self._handler.open_order(order)

        assert result is False, "open_order should return False with invalid parameters"

        self._log.info("Invalid order correctly rejected")

    # ───────────────────────────────────────────────────────────
    # PRIVATE METHODS
    # ───────────────────────────────────────────────────────────
    def _wait_for_order_execution(self, order: "OrderModel") -> None:
        """Wait for order to reach OPEN status with polling timeout.

        Polls the order status until it reaches OPEN status or the polling
        timeout is reached. Checks both the order status directly and the
        polling task completion status.

        Args:
            order: OrderModel instance to wait for execution.

        Raises:
            TimeoutError: If order does not reach OPEN status within
                _POLLING_TIMEOUT_SECONDS.
        """
        self._log.info(f"Waiting for order {order.id} to be executed (max {self._POLLING_TIMEOUT_SECONDS}s)")

        start_time = time.time()
        polling_tasks = getattr(self._handler, "_polling_tasks", {})

        while time.time() - start_time < self._POLLING_TIMEOUT_SECONDS:
            if order.status == OrderStatus.OPEN:
                elapsed = time.time() - start_time
                self._log.info(f"Order executed after {elapsed:.1f}s")
                return

            if order.id in polling_tasks:
                task = polling_tasks[order.id]
                if task.done():
                    self._log.info("Polling task completed")
                    return

            time.sleep(1)

        raise TimeoutError(
            f"Order {order.id} did not reach OPEN status within {self._POLLING_TIMEOUT_SECONDS} seconds",
        )
