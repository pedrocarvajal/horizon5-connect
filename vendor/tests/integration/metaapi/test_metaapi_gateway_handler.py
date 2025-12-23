"""Integration tests for MetaAPI GatewayHandler operations."""

import datetime
import time
from typing import Optional

from vendor.configs.timezone import TIMEZONE
from vendor.enums.order_side import OrderSide
from vendor.enums.order_status import OrderStatus
from vendor.enums.order_type import OrderType
from vendor.models.order import OrderModel
from vendor.services.orderbook.gateway import GatewayHandlerService
from vendor.tests.integration.metaapi.wrappers.metaapi import MetaApiWrapper


class TestMetaApiGatewayHandler(MetaApiWrapper):
    """Integration tests for GatewayHandler with MetaAPI."""

    _POLLING_TIMEOUT_SECONDS: int = 70
    _DEFAULT_VOLUME: float = 0.01

    def __init__(self, method_name: str = "runTest") -> None:
        super().__init__(method_name)
        self._handler: GatewayHandlerService

    def setUp(self) -> None:
        super().setUp()
        self._handler = GatewayHandlerService(
            gateway=self._gateway,
            backtest=False,
        )

    def test_place_order_returns_gateway_execution_price(self) -> None:
        """Test that place_order updates order.price with gateway execution price."""
        order = self._build_order_model(
            symbol=self._SYMBOL,
            side=OrderSide.BUY,
            volume=self._DEFAULT_VOLUME,
        )

        initial_price = order.price
        result = self._handler.place_order(order)

        assert result is True, "place_order should return True"
        assert order.gateway_order_id is not None, "Order should have gateway_order_id"

        self._wait_for_order_status(order, OrderStatus.OPEN)

        assert order.status == OrderStatus.OPEN, f"Order should be OPEN, got {order.status}"
        assert order.price > 0, "Order price should be set from gateway"

        if initial_price == 0:
            assert order.price > 0, "Order price should be updated from gateway execution"

        self._log.info(f"Order opened: gateway_id={order.gateway_order_id}, execution_price={order.price}")

        self._close_position_by_id(order.gateway_order_id)

    def test_close_position_returns_gateway_execution_price(self) -> None:
        """Test that close_position updates order.close_price with gateway execution price."""
        order = self._build_order_model(
            symbol=self._SYMBOL,
            side=OrderSide.BUY,
            volume=self._DEFAULT_VOLUME,
        )

        open_result = self._handler.place_order(order)
        assert open_result is True, "Order should open successfully"

        self._wait_for_order_status(order, OrderStatus.OPEN)
        assert order.status == OrderStatus.OPEN, "Order should be OPEN before closing"

        open_price = order.price
        opening_gateway_id = order.gateway_order_id

        close_result = self._handler.close_position(order)
        assert close_result is True, "close_position should return True"
        assert order.gateway_order_id != opening_gateway_id, "Close should have different gateway_order_id"

        self._wait_for_order_status(order, OrderStatus.CLOSED)

        assert order.status == OrderStatus.CLOSED, f"Order should be CLOSED, got {order.status}"
        assert order.close_price > 0, "Order close_price should be set from gateway"

        self._log.info(f"Order closed: open_price={open_price}, close_price={order.close_price}")

    def test_sync_orders_detects_manual_close(self) -> None:
        """Test that sync_orders detects when a position is closed manually."""
        order = self._build_order_model(
            symbol=self._SYMBOL,
            side=OrderSide.BUY,
            volume=self._DEFAULT_VOLUME,
        )

        open_result = self._handler.place_order(order)
        assert open_result is True, "Order should open successfully"

        self._wait_for_order_status(order, OrderStatus.OPEN)
        assert order.status == OrderStatus.OPEN, "Order should be OPEN"

        position_id = order.gateway_order_id
        self._log.info(f"Order opened with position_id: {position_id}")

        sync_result_before = self._handler.sync_orders({order.id: order})
        assert order.id not in sync_result_before, "Order should exist in gateway before manual close"

        self._log.info("Closing position manually via gateway...")
        self._close_position_by_id(position_id)

        time.sleep(2)

        sync_result_after = self._handler.sync_orders({order.id: order})

        assert order.id in sync_result_after, "sync_orders should detect manual close"

        close_info = sync_result_after[order.id]
        assert close_info.exists is False, "Position should not exist after manual close"
        assert close_info.status == OrderStatus.CLOSED, "Status should be CLOSED"
        assert close_info.close_price > 0, "Close price should be set"

        self._log.info(f"Manual close detected: close_price={close_info.close_price}, profit={close_info.profit}")

    def test_update_order_returns_current_state(self) -> None:
        """Test that update_order returns current state from gateway."""
        order = self._build_order_model(
            symbol=self._SYMBOL,
            side=OrderSide.BUY,
            volume=self._DEFAULT_VOLUME,
        )

        open_result = self._handler.place_order(order)
        assert open_result is True, "Order should open successfully"

        self._wait_for_order_status(order, OrderStatus.OPEN)

        result = self._handler.update_order(order)

        assert result.exists is True, "Position should exist"
        assert result.status == OrderStatus.OPEN, "Status should be OPEN"

        self._log.info(f"update_order result: exists={result.exists}, status={result.status}")

        self._close_position_by_id(order.gateway_order_id)

    def test_open_close_full_lifecycle(self) -> None:
        """Test full order lifecycle: open -> verify prices -> close -> verify prices."""
        order = self._build_order_model(
            symbol=self._SYMBOL,
            side=OrderSide.BUY,
            volume=self._DEFAULT_VOLUME,
        )

        open_result = self._handler.place_order(order)
        assert open_result is True, "Order should open"

        self._wait_for_order_status(order, OrderStatus.OPEN)
        assert order.status == OrderStatus.OPEN, "Order should be OPEN"
        assert order.price > 0, "Open price should be from gateway"

        open_price = order.price
        self._log.info(f"Open price from gateway: {open_price}")

        close_result = self._handler.close_position(order)
        assert close_result is True, "Order should close"

        self._wait_for_order_status(order, OrderStatus.CLOSED)
        assert order.status == OrderStatus.CLOSED, "Order should be CLOSED"
        assert order.close_price > 0, "Close price should be from gateway"

        close_price = order.close_price
        self._log.info(f"Close price from gateway: {close_price}")

        if order.side == OrderSide.BUY:
            expected_profit = (close_price - open_price) * order.executed_volume
        else:
            expected_profit = (open_price - close_price) * order.executed_volume

        self._log.info(
            f"Full lifecycle complete: open={open_price}, close={close_price}, expected_profit={expected_profit:.2f}"
        )

    def _build_order_model(
        self,
        symbol: str,
        side: OrderSide,
        volume: float,
        price: float = 0.0,
    ) -> OrderModel:
        return OrderModel(
            symbol=symbol,
            side=side,
            order_type=OrderType.MARKET,
            volume=volume,
            price=price,
            backtest=False,
            gateway=self._gateway,
            created_at=datetime.datetime.now(tz=TIMEZONE),
            updated_at=datetime.datetime.now(tz=TIMEZONE),
        )

    def _wait_for_order_status(
        self,
        order: OrderModel,
        target_status: OrderStatus,
        timeout_seconds: int = 70,
    ) -> None:
        self._log.info(f"Waiting for order {order.id} to reach {target_status}")
        start_time = time.time()

        polling_tasks = getattr(self._handler, "_polling_tasks", {})

        while time.time() - start_time < timeout_seconds:
            if order.status == target_status:
                elapsed = time.time() - start_time
                self._log.info(f"Order reached {target_status} after {elapsed:.1f}s")
                return

            if order.id in polling_tasks:
                task = polling_tasks[order.id]
                if task.done():
                    self._log.info("Polling task completed")
                    if order.status == target_status:
                        return

            time.sleep(1)

        raise TimeoutError(
            f"Order {order.id} did not reach {target_status} within {timeout_seconds}s. Current status: {order.status}"
        )

    def _close_position_by_id(self, position_id: Optional[str]) -> None:
        if not position_id:
            return

        try:
            result = self._gateway.close_position(position_id=position_id)
            if result:
                self._log.info(f"Position {position_id} closed")
            else:
                self._log.warning(f"Failed to close position {position_id}, trying fallback")
                positions = self._gateway.get_positions(symbol=self._SYMBOL)
                for pos in positions:
                    if pos.response and str(pos.response.get("id")) == position_id:
                        close_side = OrderSide.SELL if pos.side == OrderSide.BUY else OrderSide.BUY
                        self._gateway.place_order(
                            symbol=self._SYMBOL,
                            side=close_side,
                            order_type=OrderType.MARKET,
                            volume=abs(pos.volume),
                        )
                        self._log.info("Position closed via opposite order")
                        break
        except Exception as e:
            self._log.warning(f"Error closing position: {e}")
