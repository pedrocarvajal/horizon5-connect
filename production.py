import argparse
from multiprocessing import Process, Queue
from typing import Any

from services.commands import CommandsService
from services.production import ProductionService


class Production(ProductionService):
    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.setup()
        self.run()


class Commands(CommandsService):
    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)


if __name__ == "__main__":
    commands_queue = Queue()
    events_queue = Queue()

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--portfolio-path",
        required=True,
    )

    args = parser.parse_args()

    processes = [
        Process(
            target=Production,
            kwargs={
                "commands_queue": commands_queue,
                "events_queue": events_queue,
                "portfolio_path": args.portfolio_path,
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
