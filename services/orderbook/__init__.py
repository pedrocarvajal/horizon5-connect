from multiprocessing import Queue
from typing import Any, Optional

from enums.order_event import OrderEvent
from services.logging import LoggingService


class OrderbookService:
    _orders_commands_queue: Optional[Queue]
    _orders_events_queue: Optional[Queue]

    def __init__(self, **kwargs: Any) -> None:
        self._orders_commands_queue: Queue = kwargs.get("orders_commands_queue")
        self._orders_events_queue: Queue = kwargs.get("orders_events_queue")

        self._log = LoggingService()
        self._log.setup("orderbook_service")
        self._log.info("Orderbook service started")

        self._check_orders_queue()

    def _check_orders_queue(self) -> None:
        if self._orders_commands_queue is None:
            self._log.error("Orders commands queue is not set")
            return

        if self._orders_events_queue is None:
            self._log.error("Orders events queue is not set")
            return

        while True:
            command = self._orders_commands_queue.get()
            event_name = command.get("event")
            order = command.get("order")
            tick = command.get("tick")

            if event_name == OrderEvent.OPEN_ORDER:
                order.open(executed_from_orderbook=True)

            elif event_name == OrderEvent.CLOSE_ORDER:
                if not tick:
                    self._log.error("Tick is not set")
                    continue

                order.close(tick=tick, executed_from_orderbook=True)

            self._orders_events_queue.put(
                {
                    "event": event_name,
                    "order": order,
                }
            )
