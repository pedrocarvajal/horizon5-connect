# Code reviewed on 2025-11-21 by Pedro Carvajal

import datetime
import time
from typing import TYPE_CHECKING, Optional

from configs.timezone import TIMEZONE
from enums.order_side import OrderSide
from enums.order_status import OrderStatus
from enums.order_type import OrderType
from models.order import OrderModel
from services.strategy.handlers.gateway import GatewayHandler
from tests.integration.binance.wrappers.binance import BinanceWrapper

if TYPE_CHECKING:
    from services.strategy.handlers.gateway import GatewayHandler


class TestGatewayHandler(BinanceWrapper):
    # ───────────────────────────────────────────────────────────
    # CONSTANTS
    # ───────────────────────────────────────────────────────────
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
        """Test GatewayHandler initialization succeeds with valid gateway."""
        assert self._handler is not None, "Handler should be initialized"
        assert self._handler._gateway is not None, "Handler should have gateway"
        assert self._handler._backtest is False, "Handler should not be in backtest mode"

    def test_open_order_market_with_polling(self) -> None:
        """Test open_order executes successfully with market order and status polling."""
        order = self._build_order_model(
            symbol=self._SYMBOL,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            volume=self._DEFAULT_ORDER_VOLUME,
        )

        result = self._handler.open_order(order)

        assert result is True, "open_order should return True for production mode"
        assert order.gateway_order_id is not None, "Order should have gateway_order_id"
        assert order.gateway_order_id != "", "Gateway order ID should not be empty"
        valid_statuses = [OrderStatus.OPENING, OrderStatus.OPEN]
        status_message = f"Order status should be OPENING or OPEN, got {order.status}"
        assert order.status in valid_statuses, status_message

        self._wait_for_order_status(
            order=order,
            target_status=OrderStatus.OPEN,
            timeout_seconds=self._POLLING_TIMEOUT_SECONDS,
            handler=self._handler,
        )

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
            for trade in order.trades:
                assert trade.price > 0, "Trade price should be > 0"
                assert trade.volume > 0, "Trade volume should be > 0"

        self._delete_order_by_id(symbol=self._SYMBOL, order_id=order.gateway_order_id)

    def test_open_order_backtest_mode(self) -> None:
        """Test open_order returns False when handler is in backtest mode."""
        handler_backtest = GatewayHandler(
            gateway=self._gateway,
            backtest=True,
            backtest_id=self._DEFAULT_ORDER_BACKTEST_ID,
        )

        order = self._build_order_model(
            symbol=self._SYMBOL,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            volume=self._DEFAULT_ORDER_VOLUME,
            backtest=True,
        )

        result = handler_backtest.open_order(order)

        expected_result = False
        message = "open_order should return False in backtest mode"

        assert result is expected_result, message
        assert order.gateway_order_id is None, "Order should not have gateway_order_id"

    def test_open_order_with_invalid_gateway_response(self) -> None:
        """Test open_order returns False when invalid parameters cause gateway rejection."""
        order = self._build_order_model(
            symbol=self._DEFAULT_ORDER_INVALID_SYMBOL,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            volume=self._DEFAULT_ORDER_INVALID_VOLUME,
        )

        result = self._handler.open_order(order)

        assert result is False, "open_order should return False with invalid parameters"

    def test_close_order_buy_position_with_polling(self) -> None:
        """Test close_order successfully closes a BUY position with SELL order and status polling."""
        order = self._build_order_model(
            symbol=self._SYMBOL,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            volume=self._DEFAULT_ORDER_VOLUME,
        )

        open_result = self._handler.open_order(order)
        assert open_result is True, "Order should open successfully"

        self._wait_for_order_status(
            order=order,
            target_status=OrderStatus.OPEN,
            timeout_seconds=self._POLLING_TIMEOUT_SECONDS,
            handler=self._handler,
        )

        assert order.status == OrderStatus.OPEN, f"Order should be OPEN before closing, got {order.status}"
        assert order.executed_volume > 0, "Order should have executed volume"

        opening_order_id = order.gateway_order_id
        close_result = self._handler.close_order(order)

        assert close_result is True, "close_order should return True"
        assert order.gateway_order_id != opening_order_id, "Close order should have different gateway_order_id"
        valid_closing_statuses = [OrderStatus.CLOSING, OrderStatus.CLOSED]
        status_message = f"Order status should be CLOSING or CLOSED, got {order.status}"
        assert order.status in valid_closing_statuses, status_message

        if order.status != OrderStatus.CLOSED:
            self._wait_for_order_status(
                order=order,
                target_status=OrderStatus.CLOSED,
                timeout_seconds=self._POLLING_TIMEOUT_SECONDS,
                handler=self._handler,
            )

        assert order.status == OrderStatus.CLOSED, f"Order should be CLOSED, got {order.status}"
        assert order.updated_at is not None, "Order should have updated_at timestamp"

        if order.close_price == 0:
            self._log.warning("Order close_price is 0, checking trades for price")

        if order.trades:
            for trade in order.trades:
                assert trade.price > 0, "Trade price should be > 0"
                assert trade.volume > 0, "Trade volume should be > 0"
        else:
            self._log.warning("Order has no trades recorded")

    def test_close_order_sell_position_with_polling(self) -> None:
        """Test close_order successfully closes a SELL position with BUY order and status polling."""
        order = self._build_order_model(
            symbol=self._SYMBOL,
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            volume=self._DEFAULT_ORDER_VOLUME,
        )

        open_result = self._handler.open_order(order)
        assert open_result is True, "Order should open successfully"

        self._wait_for_order_status(
            order=order,
            target_status=OrderStatus.OPEN,
            timeout_seconds=self._POLLING_TIMEOUT_SECONDS,
            handler=self._handler,
        )

        assert order.status == OrderStatus.OPEN, f"Order should be OPEN before closing, got {order.status}"
        assert order.executed_volume > 0, "Order should have executed volume"

        opening_order_id = order.gateway_order_id
        close_result = self._handler.close_order(order)

        assert close_result is True, "close_order should return True"
        assert order.gateway_order_id != opening_order_id, "Close order should have different gateway_order_id"
        valid_closing_statuses = [OrderStatus.CLOSING, OrderStatus.CLOSED]
        status_message = f"Order status should be CLOSING or CLOSED, got {order.status}"
        assert order.status in valid_closing_statuses, status_message

        if order.status != OrderStatus.CLOSED:
            self._wait_for_order_status(
                order=order,
                target_status=OrderStatus.CLOSED,
                timeout_seconds=self._POLLING_TIMEOUT_SECONDS,
                handler=self._handler,
            )

        assert order.status == OrderStatus.CLOSED, f"Order should be CLOSED, got {order.status}"
        assert order.updated_at is not None, "Order should have updated_at timestamp"

        if order.close_price == 0:
            self._log.warning("Order close_price is 0, checking trades for price")

        if order.trades:
            for trade in order.trades:
                assert trade.price > 0, "Trade price should be > 0"
                assert trade.volume > 0, "Trade volume should be > 0"
        else:
            self._log.warning("Order has no trades recorded")

    def test_close_order_backtest_mode(self) -> None:
        """Test close_order returns False when handler is in backtest mode."""
        handler_backtest = GatewayHandler(
            gateway=self._gateway,
            backtest=True,
            backtest_id=self._DEFAULT_ORDER_BACKTEST_ID,
        )

        order = self._build_order_model(
            symbol=self._SYMBOL,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            volume=self._DEFAULT_ORDER_VOLUME,
            backtest=True,
        )

        order.status = OrderStatus.OPEN
        order.executed_volume = self._DEFAULT_ORDER_VOLUME

        result = handler_backtest.close_order(order)

        expected_result = False
        message = "close_order should return False in backtest mode"

        assert result is expected_result, message

    # ───────────────────────────────────────────────────────────
    # PRIVATE HELPERS
    # ───────────────────────────────────────────────────────────
    def _build_order_model(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        volume: float,
        price: float = 0.0,
        backtest: bool = False,
    ) -> OrderModel:
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

    def _wait_for_order_status(
        self,
        order: "OrderModel",
        target_status: OrderStatus,
        timeout_seconds: int = 70,
        handler: Optional["GatewayHandler"] = None,
    ) -> None:
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
