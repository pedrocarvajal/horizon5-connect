from multiprocessing import Queue
from threading import Thread
from typing import Dict, List

from enums.order_event import OrderEvent
from models.order import OrderModel
from services.logging import LoggingService


class OrderbookHandler:
    _orders: List[Dict[str, OrderModel]]
    _orders_commands_queue: Queue
    _orders_events_queue: Queue

    def __init__(
        self,
        orders_commands_queue: Queue,
        orders_events_queue: Queue,
    ) -> None:
        self._log = LoggingService()
        self._log.setup("orderbook_handler")

        self._orders_commands_queue = orders_commands_queue
        self._orders_events_queue = orders_events_queue

        self._thread = Thread(target=self.listen)
        self._thread.daemon = True
        self._thread.start()

    def listen(self) -> None:
        while True:
            event = self._orders_events_queue.get()
            event_name = event.get("event")

            if event_name == OrderEvent.OPENED:
                self._log.info(f"Received event: {event}")

    def push(self, order: OrderModel) -> None:
        if self._orders_commands_queue is None:
            self._log.error("Orders commands queue is not set")
            return

        self._orders_commands_queue.put(
            {
                "order": order,
                "event": OrderEvent.OPEN,
            }
        )
