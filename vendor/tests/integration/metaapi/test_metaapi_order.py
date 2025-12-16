"""Integration tests for MetaAPI order operations."""

from typing import Optional

from vendor.enums.order_side import OrderSide
from vendor.enums.order_type import OrderType
from vendor.services.gateway.models.enums.gateway_order_status import GatewayOrderStatus
from vendor.services.gateway.models.gateway_order import GatewayOrderModel
from vendor.tests.integration.metaapi.wrappers.metaapi import MetaApiWrapper


class TestMetaApiOrder(MetaApiWrapper):
    """Integration tests for MetaAPI order operations."""

    _DEFAULT_VOLUME: float = 0.01

    def setUp(self) -> None:
        super().setUp()

    def test_place_order_market(self) -> None:
        """Test placing a market order."""
        order = self._place_test_order(
            symbol=self._SYMBOL,
            side=OrderSide.BUY,
            volume=self._DEFAULT_VOLUME,
        )
        self._assert_order_is_valid(order=order, expected_type=OrderType.MARKET)
        assert order is not None
        self._close_position_for_order(order=order)

    def test_get_orders(self) -> None:
        """Test retrieving pending orders."""
        orders = self._gateway.get_orders()
        assert orders is not None, "Orders should not be None"
        assert isinstance(orders, list), "Orders should be a list"
        assert all(isinstance(o, GatewayOrderModel) for o in orders), "All orders should be GatewayOrderModel"
        for order in orders:
            assert order.id != "", "Order ID should not be empty"
            assert order.response is not None, "Order response should not be None"
        self._log.info(f"Total pending orders found: {len(orders)}")

    def test_get_orders_by_symbol(self) -> None:
        """Test retrieving pending orders filtered by symbol."""
        orders = self._gateway.get_orders(symbol=self._SYMBOL)
        assert orders is not None, "Orders should not be None"
        assert isinstance(orders, list), "Orders should be a list"
        for order in orders:
            assert order.symbol.upper() == self._SYMBOL.upper(), f"Symbol should be {self._SYMBOL}"
        self._log.info(f"Total pending orders for {self._SYMBOL}: {len(orders)}")

    def _place_test_order(
        self,
        symbol: str,
        side: OrderSide,
        volume: float,
    ) -> Optional[GatewayOrderModel]:
        """Place a test market order."""
        return self._gateway.place_order(
            symbol=symbol,
            side=side,
            order_type=OrderType.MARKET,
            volume=volume,
        )

    def _assert_order_is_valid(
        self,
        order: Optional[GatewayOrderModel],
        expected_type: OrderType,
        expected_symbol: Optional[str] = None,
    ) -> None:
        """Assert that the order is valid."""
        if expected_symbol is None:
            expected_symbol = self._SYMBOL
        assert order is not None, "Order should not be None"
        assert isinstance(order, GatewayOrderModel), "Order should be a GatewayOrderModel"
        assert order.id != "", "Order ID should not be empty"
        assert order.symbol.upper() == expected_symbol.upper(), f"Symbol should be {expected_symbol}"
        assert order.order_type == expected_type, f"Order type should be {expected_type}"
        assert order.volume > 0, "Volume should be > 0"
        assert order.executed_volume >= 0, "Executed volume should be >= 0"
        if expected_type.is_market():
            assert order.status in [
                GatewayOrderStatus.PENDING,
                GatewayOrderStatus.EXECUTED,
            ], "Status should be PENDING or EXECUTED"
        assert order.response is not None, "Response should not be None"

    def _close_position_for_order(
        self,
        order: GatewayOrderModel,
    ) -> None:
        """Close the position created by the order."""
        if order.status != GatewayOrderStatus.EXECUTED:
            self._log.info(f"Order {order.id} not executed, skipping position close")
            return

        positions = self._gateway.get_positions(symbol=order.symbol)
        if len(positions) == 0:
            self._log.warning(f"No position found for order {order.id}")
            return

        position = positions[0]
        if position.volume == 0:
            self._log.info(f"No position to close for order {order.id}")
            return

        position_id = position.response.get("id") if position.response else None
        if position_id:
            close_result = self._gateway.close_position(position_id=position_id)
            if close_result:
                self._log.info(f"Position closed for order {order.id}")
            else:
                close_side = OrderSide.SELL if order.side == OrderSide.BUY else OrderSide.BUY
                close_volume = abs(position.volume)
                self._gateway.place_order(
                    symbol=order.symbol,
                    side=close_side,
                    order_type=OrderType.MARKET,
                    volume=close_volume,
                )
                self._log.info(f"Position closed via opposite order for {order.id}")
