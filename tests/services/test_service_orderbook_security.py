import threading
from unittest.mock import Mock, patch

from enums.order_side import OrderSide
from enums.order_status import OrderStatus
from models.order import OrderModel
from services.gateway.models.enums.gateway_order_status import GatewayOrderStatus
from services.gateway.models.gateway_order import GatewayOrderModel
from services.gateway.models.gateway_symbol_info import GatewaySymbolInfoModel
from tests.services.wrappers.orderbook import OrderbookWrapper


class TestServiceOrderbookSecurity(OrderbookWrapper):
    def test_async_get_trades_exception_handled(self) -> None:
        orderbook = self._create_orderbook(balance=10000.0)
        tick = self._create_tick(50000.0)
        orderbook.refresh(tick)
        order = self._create_order()
        orderbook._backtest = False
        with patch.object(
            orderbook._gateway_handler._gateway, "get_trades", side_effect=Exception("Simulated get_trades error")
        ):
            gateway_order = GatewayOrderModel(
                id="gw-123",
                symbol="BTCUSDT",
                side=OrderSide.BUY,
                price=50000.0,
                executed_volume=0.01,
                status=GatewayOrderStatus.EXECUTED,
            )
            orderbook._gateway_handler._handle_executed_order(order, gateway_order)
        assert order.status == OrderStatus.OPEN
        assert order.executed_volume == 0.01

    def test_validate_empty_symbol_rejected(self) -> None:
        orderbook = self._create_orderbook()
        orderbook._backtest = False
        order = self._create_order()
        order.symbol = ""
        result = orderbook._gateway_handler._validate_order_parameters(order)
        assert result is False

    def test_validate_symbol_too_long_rejected(self) -> None:
        orderbook = self._create_orderbook()
        orderbook._backtest = False
        order = self._create_order()
        order.symbol = "A" * 25
        result = orderbook._gateway_handler._validate_order_parameters(order)
        assert result is False

    def test_validate_volume_below_minimum_rejected(self) -> None:
        orderbook = self._create_orderbook()
        orderbook._backtest = False
        symbol_info = GatewaySymbolInfoModel(
            symbol="BTCUSDT",
            min_quantity=0.001,
            max_quantity=1000.0,
            min_price=0.01,
            max_price=1000000.0,
            min_notional=10.0,
        )
        with patch.object(orderbook._gateway_handler._gateway, "get_symbol_info", return_value=symbol_info):
            order = self._create_order(volume=0.0001)
            result = orderbook._gateway_handler._validate_order_parameters(order)
            assert result is False

    def test_validate_volume_above_maximum_rejected(self) -> None:
        orderbook = self._create_orderbook()
        orderbook._backtest = False
        symbol_info = GatewaySymbolInfoModel(
            symbol="BTCUSDT",
            min_quantity=0.001,
            max_quantity=1000.0,
            min_price=0.01,
            max_price=1000000.0,
            min_notional=10.0,
        )
        with patch.object(orderbook._gateway_handler._gateway, "get_symbol_info", return_value=symbol_info):
            order = self._create_order(volume=2000.0)
            result = orderbook._gateway_handler._validate_order_parameters(order)
            assert result is False

    def test_validate_price_below_minimum_rejected(self) -> None:
        orderbook = self._create_orderbook()
        orderbook._backtest = False
        symbol_info = GatewaySymbolInfoModel(
            symbol="BTCUSDT",
            min_quantity=0.001,
            max_quantity=1000.0,
            min_price=0.01,
            max_price=1000000.0,
            min_notional=10.0,
        )
        with patch.object(orderbook._gateway_handler._gateway, "get_symbol_info", return_value=symbol_info):
            order = self._create_order(price=0.005)
            result = orderbook._gateway_handler._validate_order_parameters(order)
            assert result is False

    def test_validate_price_above_maximum_rejected(self) -> None:
        orderbook = self._create_orderbook()
        orderbook._backtest = False
        symbol_info = GatewaySymbolInfoModel(
            symbol="BTCUSDT",
            min_quantity=0.001,
            max_quantity=1000.0,
            min_price=0.01,
            max_price=1000000.0,
            min_notional=10.0,
        )
        with patch.object(orderbook._gateway_handler._gateway, "get_symbol_info", return_value=symbol_info):
            order = self._create_order(price=2000000.0)
            result = orderbook._gateway_handler._validate_order_parameters(order)
            assert result is False

    def test_validate_notional_below_minimum_rejected(self) -> None:
        orderbook = self._create_orderbook()
        orderbook._backtest = False
        symbol_info = GatewaySymbolInfoModel(
            symbol="BTCUSDT",
            min_quantity=0.001,
            max_quantity=1000.0,
            min_price=0.01,
            max_price=1000000.0,
            min_notional=100.0,
        )
        with patch.object(orderbook._gateway_handler._gateway, "get_symbol_info", return_value=symbol_info):
            order = self._create_order(volume=0.001, price=50.0)
            result = orderbook._gateway_handler._validate_order_parameters(order)
            assert result is False

    def test_validate_valid_order_accepted(self) -> None:
        orderbook = self._create_orderbook()
        orderbook._backtest = False
        symbol_info = GatewaySymbolInfoModel(
            symbol="BTCUSDT",
            min_quantity=0.001,
            max_quantity=1000.0,
            min_price=0.01,
            max_price=1000000.0,
            min_notional=10.0,
        )
        with patch.object(orderbook._gateway_handler._gateway, "get_symbol_info", return_value=symbol_info):
            order = self._create_order(volume=0.01, price=50000.0)
            result = orderbook._gateway_handler._validate_order_parameters(order)
            assert result is True

    def test_symbol_info_cached_after_first_request(self) -> None:
        orderbook = self._create_orderbook()
        orderbook._backtest = False
        symbol_info = GatewaySymbolInfoModel(symbol="BTCUSDT")
        mock_get_symbol_info = Mock(return_value=symbol_info)
        with patch.object(orderbook._gateway_handler._gateway, "get_symbol_info", mock_get_symbol_info):
            orderbook._gateway_handler._get_symbol_info("BTCUSDT")
            orderbook._gateway_handler._get_symbol_info("BTCUSDT")
            orderbook._gateway_handler._get_symbol_info("BTCUSDT")
        assert mock_get_symbol_info.call_count == 1

    def test_concurrent_open_orders_no_over_leverage(self) -> None:
        orderbook = self._create_orderbook(balance=1000.0, leverage=10)
        tick = self._create_tick(50000.0)
        orderbook.refresh(tick)
        initial_balance = orderbook.balance
        results = []

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
            order.volume * order.price / orderbook._leverage for order in results if order.status == OrderStatus.OPEN
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
        orders = []
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
        results = []

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
        orderbook._backtest = False
        tick = self._create_tick(50000.0)
        orderbook.refresh(tick)
        initial_balance = orderbook.balance
        with patch.object(orderbook._gateway_handler, "open_order", return_value=False):
            order = self._create_order(volume=0.01, price=50000.0)
            orderbook.open(order)
        assert order.status == OrderStatus.CANCELLED
        assert abs(orderbook.balance - initial_balance) < self._EPSILON

    def test_close_order_gateway_failure_reverts_balance(self) -> None:
        orderbook = self._create_orderbook(balance=10000.0)
        orderbook._backtest = False
        tick = self._create_tick(50000.0)
        orderbook.refresh(tick)
        order = self._create_order(volume=0.01, price=50000.0)
        with patch.object(orderbook._gateway_handler, "open_order", return_value=True):
            orderbook.open(order)
        order.status = OrderStatus.OPEN
        profit_tick = self._create_tick(51000.0)
        orderbook.refresh(profit_tick)
        balance_before_close = orderbook.balance
        with patch.object(orderbook._gateway_handler, "close_order", return_value=False):
            orderbook.close(order)
        assert order.status == OrderStatus.OPEN
        assert abs(orderbook.balance - balance_before_close) < self._EPSILON

    def test_multiple_gateway_failures_tracked_correctly(self) -> None:
        orderbook = self._create_orderbook(balance=10000.0)
        orderbook._backtest = False
        tick = self._create_tick(50000.0)
        orderbook.refresh(tick)
        initial_balance = orderbook.balance
        with patch.object(orderbook._gateway_handler, "open_order", return_value=False):
            for _ in range(5):
                order = self._create_order(volume=0.01, price=50000.0)
                orderbook.open(order)
        assert abs(orderbook.balance - initial_balance) < self._EPSILON
        cancelled_orders = [o for o in orderbook.orders if o.status == OrderStatus.CANCELLED]
        assert len(cancelled_orders) == 5
