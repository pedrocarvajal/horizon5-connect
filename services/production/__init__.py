import time
from multiprocessing import Queue
from typing import Any

from services.logging import LoggingService


class ProductionService:
    _commands_queue: Queue
    _events_queue: Queue

    def __init__(self, **kwargs: Any) -> None:
        self._log = LoggingService()
        self._log.setup("production_service")

        self._commands_queue = kwargs.get("commands_queue")
        self._events_queue = kwargs.get("events_queue")

    def setup(self) -> None:
        if not self._commands_queue:
            raise ValueError("Commands queue is required")

        if not self._events_queue:
            raise ValueError("Events queue is required")

    def run(self) -> None:
        while True:
            self._log.info("Production service running")
            time.sleep(1)
