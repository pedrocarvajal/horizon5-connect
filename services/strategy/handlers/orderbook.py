from multiprocessing import Queue
from threading import Thread
from typing import Callable, Dict, List

from enums.order_event import OrderEvent
from enums.order_status import OrderStatus
from models.order import OrderModel
from services.logging import LoggingService


class OrderbookHandler:
    _orders: List[Dict[str, OrderModel]]
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

        self._orders_commands_queue = orders_commands_queue
        self._orders_events_queue = orders_events_queue

        self._on_transaction = on_transaction

        self._thread = Thread(target=self.listen)
        self._thread.daemon = True
        self._thread.start()

    def listen(self) -> None:
        while True:
            event = self._orders_events_queue.get()
            event_name = event.get("event")
            order = event.get("order")

            if event_name is not OrderEvent.UPDATE:
                return

            if order is None:
                self._log.warning("Order is None")
                return

            if order.status is OrderStatus.ORDER_CANCELLED:
                self._log.warning(f"Order {order.id} cancelled.")
                del self._orders[order.id]

            if self._on_transaction is not None:
                self._on_transaction(order)

    def push(self, order: OrderModel) -> None:
        if self._orders_commands_queue is None:
            self._log.error("Orders commands queue is not set")
            return

        self._orders_commands_queue.put(
            {
                "order": order,
                "event": OrderEvent.PUSH,
            }
        )
