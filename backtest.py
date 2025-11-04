import datetime
from multiprocessing import Process, Queue
from typing import Any

from configs.assets import ASSETS
from configs.timezone import TIMEZONE
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
    to_date = datetime.datetime.now(tz=TIMEZONE)
    # from_date = to_date - datetime.timedelta(days=365 * 1)
    from_date = to_date - datetime.timedelta(days=30)
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
