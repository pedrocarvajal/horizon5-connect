from multiprocessing import Queue
from threading import Thread
from typing import Callable, Dict, List

from enums.order_event import OrderEvent
from enums.order_status import OrderStatus
from models.order import OrderModel
from models.tick import TickModel
from services.logging import LoggingService


class OrderbookHandler:
    _orders: Dict[str, OrderModel]
    _orders_commands_queue: Queue
    _orders_events_queue: Queue
    _on_transaction: Callable[[OrderModel], None]

    def __init__(
        self,
        orders_commands_queue: Queue,
        orders_events_queue: Queue,
        on_transaction: Callable[[OrderModel], None],
    ) -> None:
        self._log = LoggingService()
        self._log.setup("orderbook_handler")

        self._orders = {}

        self._orders_commands_queue = orders_commands_queue
        self._orders_events_queue = orders_events_queue

        self._on_transaction = on_transaction

        self._thread = Thread(target=self.listen)
        self._thread.daemon = True
        self._thread.start()

    def refresh(self, tick: TickModel) -> None:
        if self._orders_commands_queue is None:
            self._log.error("Orders commands queue is not set")
            return

        for order in list(self._orders.values()):
            ready_to_close_take_profit = order.check_if_ready_to_close_take_profit(tick)
            ready_to_close_stop_loss = order.check_if_ready_to_close_stop_loss(tick)

            if ready_to_close_take_profit or ready_to_close_stop_loss:
                self._orders[order.id].status = OrderStatus.CLOSING
                self._orders_commands_queue.put(
                    {
                        "order": order,
                        "tick": tick,
                        "event": OrderEvent.CLOSE_ORDER,
                    }
                )

            if (
                order.status in [OrderStatus.CANCELLED, OrderStatus.CLOSED]
                and order.id in self._orders
            ):
                del self._orders[order.id]

    def push(self, order: OrderModel) -> None:
        if self._orders_commands_queue is None:
            self._log.error("Orders commands queue is not set")
            return

        self._orders[order.id] = order
        self._orders_commands_queue.put(
            {
                "order": order,
                "event": OrderEvent.OPEN_ORDER,
            }
        )

    def close(self, order: OrderModel) -> None:
        if self._orders_commands_queue is None:
            self._log.error("Orders commands queue is not set")
            return

        self._orders_commands_queue.put(
            {
                "order": order,
                "event": OrderEvent.CLOSE_ORDER,
            }
        )

    def listen(self) -> None:
        while True:
            event = self._orders_events_queue.get()
            event_name = event.get("event")
            order = event.get("order")

            if event_name not in [OrderEvent.OPEN_ORDER, OrderEvent.CLOSE_ORDER]:
                continue

            if order is None:
                self._log.warning("Order is None")
                continue

            self._orders[order.id] = order
            self._on_transaction(order)

    @property
    def orders(self) -> List[OrderModel]:
        return self._orders.values()
