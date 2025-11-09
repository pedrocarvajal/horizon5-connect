from typing import Callable, Dict, List, Optional

from enums.order_side import OrderSide
from enums.order_status import OrderStatus
from models.order import OrderModel
from models.tick import TickModel
from services.logging import LoggingService


class OrderbookHandler:
    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    _allocation: float
    _balance: float
    _nav: float
    _exposure: float
    _orders: Dict[str, OrderModel]
    _tick: TickModel
    _on_transaction: Callable[[OrderModel], None]

    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(
        self,
        allocation: float,
        balance: float,
        on_transaction: Callable[[OrderModel], None],
    ) -> None:
        self._log = LoggingService()
        self._log.setup("orderbook_handler")

        self._allocation = allocation
        self._balance = balance
        self._orders = {}
        self._tick = None
        self._nav = 0.0
        self._exposure = 0.0
        self._on_transaction = on_transaction

    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def refresh(self, tick: TickModel) -> None:
        self._tick = tick

        for order in list(self._orders.values()):
            order.close_price = tick.price
            order.updated_at = tick.date

            ready_to_close_take_profit = order.check_if_ready_to_close_take_profit(tick)
            ready_to_close_stop_loss = order.check_if_ready_to_close_stop_loss(tick)

            if ready_to_close_take_profit or ready_to_close_stop_loss:
                self._orders[order.id].status = OrderStatus.CLOSING
                self.close(order)

    def clean(self) -> None:
        for order_id in list(self._orders.keys()):
            if self._orders[order_id].status in [
                OrderStatus.CLOSED,
            ]:
                del self._orders[order_id]

    def open(self, order: OrderModel) -> None:
        order.status = OrderStatus.OPENED
        order.executed_volume = order.volume

        if self._balance <= 0:
            self._log.error("Balance is less than 0, cannot open order.")
            order.status = OrderStatus.CANCELLED
            order.executed_volume = 0

        if order.volume * order.price > self._balance:
            self._log.error("Balance is less than order cost, cannot open order.")

            order.status = OrderStatus.CANCELLED
            order.executed_volume = 0

        order.updated_at = self._tick.date
        order.open()

        if order.status is OrderStatus.OPENED:
            self._balance -= order.volume * order.price

        if order.status is OrderStatus.CANCELLED:
            self._log.error(f"Order {order.id} was cancelled trying to open.")

        self._orders[order.id] = order
        self._on_transaction(order)

    def close(self, order: OrderModel) -> None:
        order.status = OrderStatus.CLOSED
        order.close_price = self._tick.price
        order.updated_at = self._tick.date
        order.close()

        if order.status is OrderStatus.CLOSED:
            self._balance += order.volume * order.price
            self._balance += order.profit

        if order.status is OrderStatus.CANCELLED:
            self._log.error(f"Order {order.id} was cancelled trying to close.")

        self._orders[order.id] = order
        self._on_transaction(order)

    def where(
        self,
        side: Optional[OrderSide] = None,
        status: Optional[OrderStatus] = None,
    ) -> List[OrderModel]:
        return [
            order
            for order in self._orders.values()
            if (side is None or order.side == side)
            and (status is None or order.status == status)
        ]

    # ───────────────────────────────────────────────────────────
    # GETTERS
    # ───────────────────────────────────────────────────────────
    @property
    def orders(self) -> List[OrderModel]:
        return list(self._orders.values())

    @property
    def balance(self) -> float:
        return self._balance

    @property
    def allocation(self) -> float:
        return self._allocation

    @property
    def nav(self) -> float:
        return self._balance + self.exposure

    @property
    def exposure(self) -> float:
        return sum(
            order.volume * order.price
            for order in self._orders.values()
            if order.status == OrderStatus.OPENED
        )
