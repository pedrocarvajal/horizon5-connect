from multiprocessing import Process, Queue
from typing import Any

from services.commands import CommandsService
from services.production import ProductionService


class Production(ProductionService):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.setup()
        self.run()


class Commands(CommandsService):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)


if __name__ == "__main__":
    commands_queue = Queue()
    events_queue = Queue()

    processes = [
        Process(
            target=Production,
            kwargs={
                "commands_queue": commands_queue,
                "events_queue": events_queue,
            },
        ),
        Process(
            target=Commands,
            kwargs={
                "commands_queue": commands_queue,
                "events_queue": events_queue,
            },
        ),
    ]

    for process in processes:
        process.start()

    for process in processes:
        process.join()
