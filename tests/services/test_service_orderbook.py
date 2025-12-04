from enums.order_side import OrderSide
from enums.order_status import OrderStatus
from tests.services.wrappers.orderbook import OrderbookWrapper


class TestServiceOrderbook(OrderbookWrapper):
    def test_initialization_with_valid_parameters(self) -> None:
        assert self._orderbook is not None
        assert self._orderbook.balance == self._INITIAL_BALANCE
        assert self._orderbook.allocation == self._INITIAL_BALANCE
        assert len(self._orderbook.orders) == 0

    def test_initialization_leverage_defaults_to_one_when_zero(self) -> None:
        orderbook = self._create_orderbook(leverage=0)
        assert orderbook.leverage == 1

    def test_initialization_leverage_defaults_to_one_when_negative(self) -> None:
        orderbook = self._create_orderbook(leverage=-5)
        assert orderbook.leverage == 1

    def test_open_order_with_sufficient_margin_succeeds(self) -> None:
        tick = self._create_tick(50000.0)
        self._orderbook.refresh(tick)
        order = self._create_order()
        self._orderbook.open(order)
        assert order.status == OrderStatus.OPEN
        assert order.executed_volume == 0.01
        assert len(self._orderbook.orders) == 1
        assert len(self._transactions) == 1

    def test_open_order_deducts_margin_from_balance(self) -> None:
        tick = self._create_tick(50000.0)
        self._orderbook.refresh(tick)
        initial_balance = self._orderbook.balance
        volume = 0.01
        price = 50000.0
        leverage = 10
        required_margin = volume * price / leverage
        order = self._create_order(volume=volume, price=price)
        self._orderbook.open(order)
        expected_balance = initial_balance - required_margin
        assert abs(self._orderbook.balance - expected_balance) < self._EPSILON

    def test_open_order_calls_transaction_callback(self) -> None:
        tick = self._create_tick(50000.0)
        self._orderbook.refresh(tick)
        order = self._create_order()
        self._orderbook.open(order)
        assert len(self._transactions) == 1
        assert self._transactions[0].id == order.id

    def test_open_order_without_tick_fails(self) -> None:
        order = self._create_order()
        self._orderbook.open(order)
        assert len(self._orderbook.orders) == 0
        assert len(self._transactions) == 0

    def test_open_order_with_zero_balance_is_cancelled(self) -> None:
        orderbook = self._create_orderbook(balance=0.0)
        tick = self._create_tick(50000.0)
        orderbook.refresh(tick)
        order = self._create_order()
        orderbook.open(order)
        assert order.status == OrderStatus.CANCELLED
        assert order.executed_volume == 0
        assert len(orderbook.orders) == 1

    def test_open_order_with_negative_balance_is_cancelled(self) -> None:
        orderbook = self._create_orderbook(balance=-100.0)
        tick = self._create_tick(50000.0)
        orderbook.refresh(tick)
        order = self._create_order()
        orderbook.open(order)
        assert order.status == OrderStatus.CANCELLED
        assert order.executed_volume == 0

    def test_open_order_with_insufficient_margin_is_cancelled(self) -> None:
        orderbook = self._create_orderbook(balance=10.0)
        tick = self._create_tick(50000.0)
        orderbook.refresh(tick)
        order = self._create_order(volume=1.0)
        orderbook.open(order)
        assert order.status == OrderStatus.CANCELLED
        assert order.executed_volume == 0

    def test_open_order_during_margin_call_is_cancelled(self) -> None:
        tick = self._create_tick(50000.0)
        self._orderbook.refresh(tick)
        self._orderbook.margin_call_active = True
        order = self._create_order()
        self._orderbook.open(order)
        assert order.status == OrderStatus.CANCELLED
        assert order.executed_volume == 0

    def test_open_order_with_low_projected_margin_level_is_cancelled(self) -> None:
        orderbook = self._create_orderbook(balance=100.0, leverage=1)
        tick = self._create_tick(50000.0)
        orderbook.refresh(tick)
        order = self._create_order(volume=0.002, price=50000.0)
        orderbook.open(order)
        assert order.status == OrderStatus.CANCELLED

    def test_close_order_returns_margin_to_balance(self) -> None:
        tick = self._create_tick(50000.0)
        self._orderbook.refresh(tick)
        order = self._create_order()
        self._orderbook.open(order)
        balance_after_open = self._orderbook.balance
        volume = 0.01
        price = 50000.0
        leverage = 10
        required_margin = volume * price / leverage
        self._orderbook.close(order)
        expected_balance = balance_after_open + required_margin
        assert abs(self._orderbook.balance - expected_balance) < self._EPSILON

    def test_close_order_applies_profit_to_balance(self) -> None:
        tick = self._create_tick(50000.0)
        self._orderbook.refresh(tick)
        order = self._create_order(side=OrderSide.BUY, price=50000.0)
        self._orderbook.open(order)
        balance_after_open = self._orderbook.balance
        closing_tick = self._create_tick(51000.0)
        self._orderbook.refresh(closing_tick)
        self._orderbook.close(order)
        profit = order.profit
        required_margin = 0.01 * 50000.0 / 10
        expected_balance = balance_after_open + required_margin + profit
        assert abs(self._orderbook.balance - expected_balance) < self._EPSILON

    def test_close_order_updates_status_to_closed(self) -> None:
        tick = self._create_tick(50000.0)
        self._orderbook.refresh(tick)
        order = self._create_order()
        self._orderbook.open(order)
        self._orderbook.close(order)
        assert order.status == OrderStatus.CLOSED

    def test_close_order_without_tick_fails(self) -> None:
        orderbook = self._create_orderbook()
        order = self._create_order()
        orderbook.close(order)
        assert order.status != OrderStatus.CLOSED

    def test_refresh_triggers_margin_call_and_closes_orders(self) -> None:
        orderbook = self._create_orderbook(balance=60.0, leverage=100)
        tick = self._create_tick(50000.0)
        orderbook.refresh(tick)
        order = self._create_order(volume=0.01, price=50000.0)
        orderbook.open(order)
        assert order.status == OrderStatus.OPEN
        first_drop = self._create_tick(30000.0)
        orderbook.refresh(first_drop)
        second_drop = self._create_tick(20000.0)
        orderbook.refresh(second_drop)
        assert order.status == OrderStatus.CLOSED
        assert len([o for o in orderbook.orders if o.status == OrderStatus.OPEN]) == 0

    def test_refresh_closes_all_orders_during_margin_call(self) -> None:
        orderbook = self._create_orderbook(balance=60.0, leverage=100)
        tick = self._create_tick(50000.0)
        orderbook.refresh(tick)
        order1 = self._create_order(volume=0.005, price=50000.0)
        orderbook.open(order1)
        order2 = self._create_order(volume=0.005, price=50000.0)
        orderbook.open(order2)
        first_drop = self._create_tick(30000.0)
        orderbook.refresh(first_drop)
        second_drop = self._create_tick(20000.0)
        orderbook.refresh(second_drop)
        open_orders = [o for o in orderbook.orders if o.status == OrderStatus.OPEN]
        assert len(open_orders) == 0

    def test_refresh_resolves_margin_call_when_recovered(self) -> None:
        orderbook = self._create_orderbook(balance=100.0, leverage=100)
        tick = self._create_tick(50000.0)
        orderbook.refresh(tick)
        order = self._create_order(volume=0.01, price=50000.0)
        orderbook.open(order)
        orderbook.margin_call_active = True
        orderbook.close(order)
        recovery_tick = self._create_tick(50000.0)
        orderbook.refresh(recovery_tick)
        assert orderbook.margin_call_active is False

    def test_refresh_closes_order_when_take_profit_reached(self) -> None:
        tick = self._create_tick(50000.0)
        self._orderbook.refresh(tick)
        order = self._create_order(side=OrderSide.BUY, price=50000.0, take_profit_price=51000.0)
        self._orderbook.open(order)
        assert order.status == OrderStatus.OPEN
        tp_tick = self._create_tick(51000.0)
        self._orderbook.refresh(tp_tick)
        assert order.status == OrderStatus.CLOSED

    def test_refresh_closes_order_when_stop_loss_reached(self) -> None:
        tick = self._create_tick(50000.0)
        self._orderbook.refresh(tick)
        order = self._create_order(side=OrderSide.BUY, price=50000.0, stop_loss_price=49000.0)
        self._orderbook.open(order)
        assert order.status == OrderStatus.OPEN
        sl_tick = self._create_tick(49000.0)
        self._orderbook.refresh(sl_tick)
        assert order.status == OrderStatus.CLOSED

    def test_refresh_updates_order_close_prices(self) -> None:
        tick = self._create_tick(50000.0)
        self._orderbook.refresh(tick)
        order = self._create_order(price=50000.0)
        self._orderbook.open(order)
        new_tick = self._create_tick(51000.0)
        self._orderbook.refresh(new_tick)
        assert order.close_price == 51000.0

    def test_where_filters_by_side(self) -> None:
        tick = self._create_tick(50000.0)
        self._orderbook.refresh(tick)
        buy_order = self._create_order(side=OrderSide.BUY)
        self._orderbook.open(buy_order)
        sell_order = self._create_order(side=OrderSide.SELL)
        self._orderbook.open(sell_order)
        buy_orders = self._orderbook.where(side=OrderSide.BUY)
        assert len(buy_orders) == 1
        assert buy_orders[0].side == OrderSide.BUY

    def test_where_filters_by_status(self) -> None:
        tick = self._create_tick(50000.0)
        self._orderbook.refresh(tick)
        order = self._create_order()
        self._orderbook.open(order)
        self._orderbook.close(order)
        open_orders = self._orderbook.where(status=OrderStatus.OPEN)
        closed_orders = self._orderbook.where(status=OrderStatus.CLOSED)
        assert len(open_orders) == 0
        assert len(closed_orders) == 1

    def test_where_filters_by_side_and_status(self) -> None:
        tick = self._create_tick(50000.0)
        self._orderbook.refresh(tick)
        buy_order = self._create_order(side=OrderSide.BUY)
        self._orderbook.open(buy_order)
        sell_order = self._create_order(side=OrderSide.SELL)
        self._orderbook.open(sell_order)
        self._orderbook.close(buy_order)
        results = self._orderbook.where(side=OrderSide.BUY, status=OrderStatus.CLOSED)
        assert len(results) == 1
        assert results[0].side == OrderSide.BUY
        assert results[0].status == OrderStatus.CLOSED

    def test_where_returns_all_orders_when_no_filters(self) -> None:
        tick = self._create_tick(50000.0)
        self._orderbook.refresh(tick)
        self._create_order()
        self._orderbook.open(self._create_order())
        self._orderbook.open(self._create_order())
        all_orders = self._orderbook.where()
        assert len(all_orders) == 2

    def test_clean_removes_closed_orders(self) -> None:
        tick = self._create_tick(50000.0)
        self._orderbook.refresh(tick)
        order1 = self._create_order()
        self._orderbook.open(order1)
        order2 = self._create_order()
        self._orderbook.open(order2)
        self._orderbook.close(order1)
        assert len(self._orderbook.orders) == 2
        self._orderbook.clean()
        assert len(self._orderbook.orders) == 1
        assert self._orderbook.orders[0].id == order2.id

    def test_clean_keeps_open_orders(self) -> None:
        tick = self._create_tick(50000.0)
        self._orderbook.refresh(tick)
        order = self._create_order()
        self._orderbook.open(order)
        self._orderbook.clean()
        assert len(self._orderbook.orders) == 1
        assert self._orderbook.orders[0].status == OrderStatus.OPEN
