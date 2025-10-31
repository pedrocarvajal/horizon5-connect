from multiprocessing import Queue
from time import sleep
from typing import Any, Optional

from interfaces.orderbook import OrderbookInterface
from services.logging import LoggingService


class OrderbookService(OrderbookInterface):
    _orders_events_queue: Optional[Queue]
    _db_queries_queue: Optional[Queue]

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        self._orders_events_queue: Queue = kwargs.get("orders_events_queue", Queue())
        self._db_queries_queue: Queue = kwargs.get("db_queries_queue", Queue())

        self._log = LoggingService()
        self._log.setup("orderbook_service")
        self._log.info("Orderbook service started")

        self._check_orders_queue()

    def _check_orders_queue(self) -> None:
        while not self._orders_events_queue.empty():
            event = self._orders_events_queue.get()
            self._log.debug(event)
            sleep(0.1)
