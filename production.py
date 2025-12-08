"""Production entry point for live trading execution."""

from __future__ import annotations

import argparse
from multiprocessing import Process, Queue
from typing import Any

from services.commands import CommandService
from services.production import ProductionService


class Production(ProductionService):
    """Production process wrapper that runs live trading."""

    def __init__(
        self,
        **kwargs: Any,
    ) -> None:
        """Initialize and start production trading execution.

        Args:
            **kwargs: Arguments passed to ProductionService.
        """
        super().__init__(**kwargs)
        self.setup()
        self.run()


class Commands(CommandService):
    """Commands process wrapper for production control."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize commands service.

        Args:
            **kwargs: Arguments passed to CommandService.
        """
        super().__init__(**kwargs)


if __name__ == "__main__":
    commands_queue: Queue[Any] = Queue()
    events_queue: Queue[Any] = Queue()

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
