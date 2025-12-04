from enums.order_status import OrderStatus
from tests.services.wrappers.orderbook import OrderbookWrapper


class TestServiceOrderbookCancel(OrderbookWrapper):
    def test_cancel_order_in_backtest_mode_releases_margin(self) -> None:
        tick = self._create_tick(50000.0)
        self._orderbook.refresh(tick)
        volume = 0.01
        price = 50000.0
        leverage = 10
        required_margin = volume * price / leverage
        order = self._create_order(volume=volume, price=price)
        self._orderbook.open(order)
        initial_balance_after_open = self._orderbook.balance
        assert order.status == OrderStatus.OPEN
        self._orderbook.cancel(order)
        assert order.status == OrderStatus.CANCELLED
        assert order.executed_volume == 0
        assert abs(self._orderbook.balance - (initial_balance_after_open + required_margin)) < self._EPSILON
        assert len(self._transactions) == 2

    def test_cancel_order_calls_transaction_callback(self) -> None:
        tick = self._create_tick(50000.0)
        self._orderbook.refresh(tick)
        order = self._create_order()
        self._orderbook.open(order)
        assert len(self._transactions) == 1
        self._orderbook.cancel(order)
        assert len(self._transactions) == 2
        assert self._transactions[1].id == order.id
        assert self._transactions[1].status == OrderStatus.CANCELLED

    def test_cancel_order_without_tick_fails(self) -> None:
        order = self._create_order()
        order.status = OrderStatus.OPEN
        self._orderbook.cancel(order)
        assert order.status == OrderStatus.OPEN

    def test_cancel_order_not_in_orderbook_fails(self) -> None:
        tick = self._create_tick(50000.0)
        self._orderbook.refresh(tick)
        order = self._create_order()
        self._orderbook.cancel(order)
        assert order.status == OrderStatus.OPENING

    def test_cancel_order_in_closing_status_fails(self) -> None:
        tick = self._create_tick(50000.0)
        self._orderbook.refresh(tick)
        order = self._create_order()
        self._orderbook.open(order)
        order.status = OrderStatus.CLOSING
        initial_balance = self._orderbook.balance
        self._orderbook.cancel(order)
        assert order.status == OrderStatus.CLOSING
        assert self._orderbook.balance == initial_balance

    def test_cancel_order_in_closed_status_fails(self) -> None:
        tick = self._create_tick(50000.0)
        self._orderbook.refresh(tick)
        order = self._create_order()
        self._orderbook.open(order)
        order.status = OrderStatus.CLOSED
        initial_balance = self._orderbook.balance
        self._orderbook.cancel(order)
        assert order.status == OrderStatus.CLOSED
        assert self._orderbook.balance == initial_balance

    def test_cancel_order_removes_from_open_orders_index(self) -> None:
        tick = self._create_tick(50000.0)
        self._orderbook.refresh(tick)
        order = self._create_order()
        self._orderbook.open(order)
        assert order.id in self._orderbook.open_orders_index
        self._orderbook.cancel(order)
        assert order.id not in self._orderbook.open_orders_index

    def test_close_order_with_zero_executed_volume_cancels(self) -> None:
        tick = self._create_tick(50000.0)
        self._orderbook.refresh(tick)
        order = self._create_order()
        self._orderbook.open(order)
        order.executed_volume = 0
        initial_balance = self._orderbook.balance
        self._orderbook.close(order)
        assert order.status == OrderStatus.CANCELLED
        assert self._orderbook.balance > initial_balance

    def test_close_partially_filled_order_releases_unfilled_margin(self) -> None:
        tick = self._create_tick(50000.0)
        self._orderbook.refresh(tick)
        volume = 0.01
        price = 50000.0
        leverage = 10
        required_margin = volume * price / leverage
        order = self._create_order(volume=volume, price=price)
        self._orderbook.open(order)
        initial_balance_after_open = self._orderbook.balance
        order.executed_volume = 0.005
        unexecuted_margin = 0.005 * price / leverage
        tick2 = self._create_tick(51000.0)
        self._orderbook.refresh(tick2)
        self._orderbook.close(order)
        expected_balance = initial_balance_after_open + unexecuted_margin + required_margin / 2 + order.profit
        assert order.status == OrderStatus.CLOSED
        assert abs(self._orderbook.balance - expected_balance) < self._EPSILON

    def test_close_partially_filled_order_updates_volume_to_executed(self) -> None:
        tick = self._create_tick(50000.0)
        self._orderbook.refresh(tick)
        volume = 0.01
        order = self._create_order(volume=volume)
        self._orderbook.open(order)
        order.executed_volume = 0.006
        tick2 = self._create_tick(51000.0)
        self._orderbook.refresh(tick2)
        self._orderbook.close(order)
        assert order.volume == 0.006
        assert order.executed_volume == 0.006

    def test_close_fully_filled_order_works_normally(self) -> None:
        tick = self._create_tick(50000.0)
        self._orderbook.refresh(tick)
        volume = 0.01
        price = 50000.0
        leverage = 10
        required_margin = volume * price / leverage
        order = self._create_order(volume=volume, price=price)
        self._orderbook.open(order)
        initial_balance_after_open = self._orderbook.balance
        tick2 = self._create_tick(51000.0)
        self._orderbook.refresh(tick2)
        self._orderbook.close(order)
        expected_balance = initial_balance_after_open + required_margin + order.profit
        assert order.status == OrderStatus.CLOSED
        assert order.executed_volume == volume
        assert abs(self._orderbook.balance - expected_balance) < self._EPSILON

    def test_cancel_order_updates_timestamp(self) -> None:
        tick = self._create_tick(50000.0)
        self._orderbook.refresh(tick)
        order = self._create_order()
        self._orderbook.open(order)
        original_updated_at = order.updated_at
        tick2 = self._create_tick(51000.0)
        self._orderbook.refresh(tick2)
        self._orderbook.cancel(order)
        assert order.updated_at != original_updated_at
        assert order.updated_at == tick2.date
