import threading
from typing import List, cast
from unittest.mock import Mock, patch

from vendor.enums.order_side import OrderSide
from vendor.enums.order_status import OrderStatus
from vendor.models.order import OrderModel
from vendor.services.gateway.models.enums.gateway_order_status import GatewayOrderStatus
from vendor.services.gateway.models.gateway_order import GatewayOrderModel
from vendor.services.gateway.models.gateway_symbol_info import GatewaySymbolInfoModel
from vendor.services.orderbook.gateway import GatewayHandlerService
from vendor.tests.services.wrappers.orderbook import OrderbookWrapper


class TestServiceOrderbookSecurity(OrderbookWrapper):
    def test_async_get_trades_exception_handled(self) -> None:
        orderbook = self._create_orderbook(balance=10000.0)
        tick = self._create_tick(50000.0)
        orderbook.refresh(tick)
        order = self._create_order()
        orderbook.is_backtest = False
        with patch.object(
            orderbook.gateway_handler.gateway, "get_trades", side_effect=Exception("Simulated get_trades error")
        ):
            gateway_order = GatewayOrderModel(
                id="gw-123",
                symbol="XAUUSD",
                side=OrderSide.BUY,
                price=50000.0,
                executed_volume=0.01,
                status=GatewayOrderStatus.EXECUTED,
            )
            handler = cast(GatewayHandlerService, orderbook.gateway_handler)
            handler._handle_executed_order(order, gateway_order)  # pyright: ignore[reportPrivateUsage]
        assert order.status == OrderStatus.OPEN
        assert order.executed_volume == 0.01

    def test_validate_empty_symbol_rejected(self) -> None:
        orderbook = self._create_orderbook()
        orderbook.is_backtest = False
        order = self._create_order()
        order.symbol = ""
        handler = cast(GatewayHandlerService, orderbook.gateway_handler)
        result = handler._validate_order_parameters(order)  # pyright: ignore[reportPrivateUsage]
        assert result is False

    def test_validate_symbol_too_long_rejected(self) -> None:
        orderbook = self._create_orderbook()
        orderbook.is_backtest = False
        order = self._create_order()
        order.symbol = "A" * 25
        handler = cast(GatewayHandlerService, orderbook.gateway_handler)
        result = handler._validate_order_parameters(order)  # pyright: ignore[reportPrivateUsage]
        assert result is False

    def test_validate_volume_below_minimum_rejected(self) -> None:
        orderbook = self._create_orderbook()
        orderbook.is_backtest = False
        symbol_info = GatewaySymbolInfoModel(
            symbol="XAUUSD",
            min_quantity=0.001,
            max_quantity=1000.0,
            min_price=0.01,
            max_price=1000000.0,
            min_notional=10.0,
        )
        handler = cast(GatewayHandlerService, orderbook.gateway_handler)
        with patch.object(orderbook.gateway_handler.gateway, "get_symbol_info", return_value=symbol_info):
            order = self._create_order(volume=0.0001)
            result = handler._validate_order_parameters(order)  # pyright: ignore[reportPrivateUsage]
            assert result is False

    def test_validate_volume_above_maximum_rejected(self) -> None:
        orderbook = self._create_orderbook()
        orderbook.is_backtest = False
        symbol_info = GatewaySymbolInfoModel(
            symbol="XAUUSD",
            min_quantity=0.001,
            max_quantity=1000.0,
            min_price=0.01,
            max_price=1000000.0,
            min_notional=10.0,
        )
        handler = cast(GatewayHandlerService, orderbook.gateway_handler)
        with patch.object(orderbook.gateway_handler.gateway, "get_symbol_info", return_value=symbol_info):
            order = self._create_order(volume=2000.0)
            result = handler._validate_order_parameters(order)  # pyright: ignore[reportPrivateUsage]
            assert result is False

    def test_validate_price_below_minimum_rejected(self) -> None:
        orderbook = self._create_orderbook()
        orderbook.is_backtest = False
        symbol_info = GatewaySymbolInfoModel(
            symbol="XAUUSD",
            min_quantity=0.001,
            max_quantity=1000.0,
            min_price=0.01,
            max_price=1000000.0,
            min_notional=10.0,
        )
        handler = cast(GatewayHandlerService, orderbook.gateway_handler)
        with patch.object(orderbook.gateway_handler.gateway, "get_symbol_info", return_value=symbol_info):
            order = self._create_order(price=0.005)
            result = handler._validate_order_parameters(order)  # pyright: ignore[reportPrivateUsage]
            assert result is False

    def test_validate_price_above_maximum_rejected(self) -> None:
        orderbook = self._create_orderbook()
        orderbook.is_backtest = False
        symbol_info = GatewaySymbolInfoModel(
            symbol="XAUUSD",
            min_quantity=0.001,
            max_quantity=1000.0,
            min_price=0.01,
            max_price=1000000.0,
            min_notional=10.0,
        )
        handler = cast(GatewayHandlerService, orderbook.gateway_handler)
        with patch.object(orderbook.gateway_handler.gateway, "get_symbol_info", return_value=symbol_info):
            order = self._create_order(price=2000000.0)
            result = handler._validate_order_parameters(order)  # pyright: ignore[reportPrivateUsage]
            assert result is False

    def test_validate_notional_below_minimum_rejected(self) -> None:
        orderbook = self._create_orderbook()
        orderbook.is_backtest = False
        symbol_info = GatewaySymbolInfoModel(
            symbol="XAUUSD",
            min_quantity=0.001,
            max_quantity=1000.0,
            min_price=0.01,
            max_price=1000000.0,
            min_notional=100.0,
        )
        handler = cast(GatewayHandlerService, orderbook.gateway_handler)
        with patch.object(orderbook.gateway_handler.gateway, "get_symbol_info", return_value=symbol_info):
            order = self._create_order(volume=0.001, price=50.0)
            result = handler._validate_order_parameters(order)  # pyright: ignore[reportPrivateUsage]
            assert result is False

    def test_validate_valid_order_accepted(self) -> None:
        orderbook = self._create_orderbook()
        orderbook.is_backtest = False
        symbol_info = GatewaySymbolInfoModel(
            symbol="XAUUSD",
            min_quantity=0.001,
            max_quantity=1000.0,
            min_price=0.01,
            max_price=1000000.0,
            min_notional=10.0,
        )
        handler = cast(GatewayHandlerService, orderbook.gateway_handler)
        with patch.object(orderbook.gateway_handler.gateway, "get_symbol_info", return_value=symbol_info):
            order = self._create_order(volume=0.01, price=50000.0)
            result = handler._validate_order_parameters(order)  # pyright: ignore[reportPrivateUsage]
            assert result is True

    def test_symbol_info_cached_after_first_request(self) -> None:
        orderbook = self._create_orderbook()
        orderbook.is_backtest = False
        symbol_info = GatewaySymbolInfoModel(symbol="XAUUSD")
        mock_get_symbol_info = Mock(return_value=symbol_info)
        handler = cast(GatewayHandlerService, orderbook.gateway_handler)
        with patch.object(orderbook.gateway_handler.gateway, "get_symbol_info", mock_get_symbol_info):
            handler._get_symbol_info("XAUUSD")  # pyright: ignore[reportPrivateUsage]
            handler._get_symbol_info("XAUUSD")  # pyright: ignore[reportPrivateUsage]
            handler._get_symbol_info("XAUUSD")  # pyright: ignore[reportPrivateUsage]
        assert mock_get_symbol_info.call_count == 1

    def test_concurrent_open_orders_no_over_leverage(self) -> None:
        orderbook = self._create_orderbook(balance=1000.0, leverage=10)
        tick = self._create_tick(50000.0)
        orderbook.refresh(tick)
        initial_balance = orderbook.balance
        results: List[OrderModel] = []

        def open_order() -> None:
            order = self._create_order(volume=0.01, price=50000.0)
            orderbook.open(order)
            results.append(order)

        threads = [threading.Thread(target=open_order) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        open_count = sum(1 for order in results if order.status == OrderStatus.OPEN)
        total_margin_used = sum(
            order.volume * order.price / orderbook.leverage for order in results if order.status == OrderStatus.OPEN
        )
        expected_balance = initial_balance - total_margin_used
        assert abs(orderbook.balance - expected_balance) < self._EPSILON
        assert orderbook.balance >= 0
        assert open_count >= 1

    def test_concurrent_balance_operations_consistent(self) -> None:
        orderbook = self._create_orderbook(balance=10000.0, leverage=10)
        tick = self._create_tick(50000.0)
        orderbook.refresh(tick)
        initial_balance = orderbook.balance
        orders: List[OrderModel] = []
        for _ in range(3):
            order = self._create_order(volume=0.01, price=50000.0)
            orderbook.open(order)
            orders.append(order)

        def close_order(order: OrderModel) -> None:
            if order.status == OrderStatus.OPEN:
                orderbook.close(order)

        threads = [threading.Thread(target=close_order, args=(order,)) for order in orders]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        final_balance = orderbook.balance
        assert abs(final_balance - initial_balance) < self._EPSILON
        assert all(order.status == OrderStatus.CLOSED for order in orders)

    def test_concurrent_property_access_no_deadlock(self) -> None:
        orderbook = self._create_orderbook(balance=10000.0)
        tick = self._create_tick(50000.0)
        orderbook.refresh(tick)
        for _ in range(5):
            orderbook.open(self._create_order())
        results: List[bool] = []

        def access_properties() -> None:
            for _ in range(100):
                _ = orderbook.balance
                _ = orderbook.nav
                _ = orderbook.equity
                _ = orderbook.exposure
                _ = orderbook.pnl
                _ = orderbook.free_margin
                _ = orderbook.used_margin
                _ = orderbook.margin_level
                _ = orderbook.orders
            results.append(True)

        threads = [threading.Thread(target=access_properties) for _ in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=5.0)
        assert len(results) == 10

    def test_open_order_gateway_failure_reverts_balance(self) -> None:
        orderbook = self._create_orderbook(balance=10000.0)
        orderbook.is_backtest = False
        tick = self._create_tick(50000.0)
        orderbook.refresh(tick)
        initial_balance = orderbook.balance
        with patch.object(orderbook.gateway_handler, "place_order", return_value=False):
            order = self._create_order(volume=0.01, price=50000.0)
            orderbook.open(order)
        assert order.status == OrderStatus.CANCELLED
        assert abs(orderbook.balance - initial_balance) < self._EPSILON

    def test_close_order_gateway_failure_reverts_balance(self) -> None:
        orderbook = self._create_orderbook(balance=10000.0)
        orderbook.is_backtest = False
        tick = self._create_tick(50000.0)
        orderbook.refresh(tick)
        order = self._create_order(volume=0.01, price=50000.0)
        with patch.object(orderbook.gateway_handler, "place_order", return_value=True):
            orderbook.open(order)
        order.status = OrderStatus.OPEN
        profit_tick = self._create_tick(51000.0)
        orderbook.refresh(profit_tick)
        balance_before_close = orderbook.balance
        with patch.object(orderbook.gateway_handler, "close_position", return_value=False):
            orderbook.close(order)
        assert order.status == OrderStatus.OPEN
        assert abs(orderbook.balance - balance_before_close) < self._EPSILON

    def test_multiple_gateway_failures_tracked_correctly(self) -> None:
        orderbook = self._create_orderbook(balance=10000.0)
        orderbook.is_backtest = False
        tick = self._create_tick(50000.0)
        orderbook.refresh(tick)
        initial_balance = orderbook.balance
        with patch.object(orderbook.gateway_handler, "place_order", return_value=False):
            for _ in range(5):
                order = self._create_order(volume=0.01, price=50000.0)
                orderbook.open(order)
        assert abs(orderbook.balance - initial_balance) < self._EPSILON
        cancelled_orders = [o for o in orderbook.orders if o.status == OrderStatus.CANCELLED]
        assert len(cancelled_orders) == 5
