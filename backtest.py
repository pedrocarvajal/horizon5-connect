import datetime
from multiprocessing import Process, Queue
from typing import Any

from configs.assets import ASSETS
from services.backtest import BacktestService
from services.commands import CommandsService


class Backtest(BacktestService):
    def __init__(
        self,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        super().run()


class Commands(CommandsService):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)


if __name__ == "__main__":
    from_date = datetime.datetime.fromisoformat("2019-01-01")
    to_date = datetime.datetime.fromisoformat("2025-11-09")

    commands_queue = Queue()
    events_queue = Queue()

    processes = [
        Process(
            target=Commands,
            kwargs={
                "commands_queue": commands_queue,
                "events_queue": events_queue,
            },
        ),
        Process(
            target=Backtest,
            kwargs={
                "asset": ASSETS["btcusdt"],
                "from_date": from_date,
                "to_date": to_date,
                "commands_queue": commands_queue,
                "events_queue": events_queue,
            },
        ),
    ]

    for process in processes:
        process.start()

    for process in processes:
        process.join()
