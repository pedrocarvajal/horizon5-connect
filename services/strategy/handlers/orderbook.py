from typing import Callable, Dict, List

from enums.order_status import OrderStatus
from models.order import OrderModel
from models.tick import TickModel
from services.logging import LoggingService


class OrderbookHandler:
    _orders: Dict[str, OrderModel]
    _tick: TickModel
    _on_transaction: Callable[[OrderModel], None]

    def __init__(
        self,
        on_transaction: Callable[[OrderModel], None],
    ) -> None:
        self._log = LoggingService()
        self._log.setup("orderbook_handler")

        self._orders = {}
        self._tick = None
        self._on_transaction = on_transaction

    def refresh(self, tick: TickModel) -> None:
        self._tick = tick

        for order in list(self._orders.values()):
            ready_to_close_take_profit = order.check_if_ready_to_close_take_profit(tick)
            ready_to_close_stop_loss = order.check_if_ready_to_close_stop_loss(tick)

            if ready_to_close_take_profit or ready_to_close_stop_loss:
                self._orders[order.id].status = OrderStatus.CLOSING
                self.close(order)

    def clean(self) -> None:
        for order_id in list(self._orders.keys()):
            if self._orders[order_id].status in [
                OrderStatus.CANCELLED,
                OrderStatus.CLOSED,
            ]:
                del self._orders[order_id]

    def open(self, order: OrderModel) -> None:
        order.updated_at = self._tick.date
        order.open()

        self._orders[order.id] = order
        self._on_transaction(order)

    def close(self, order: OrderModel) -> None:
        order.close_price = self._tick.price
        order.updated_at = self._tick.date
        order.close()

        self._orders[order.id] = order
        self._on_transaction(order)

    @property
    def orders(self) -> List[OrderModel]:
        return list(self._orders.values())
