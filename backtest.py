import datetime
from multiprocessing import Process, Queue
from typing import Any

from configs.assets import ASSETS
from configs.timezone import TIMEZONE
from services.backtest import BacktestService
from services.db import DBService


class Backtest(BacktestService):
    def __init__(
        self,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        super().run()


class DBManager(DBService):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)


if __name__ == "__main__":
    to_date = datetime.datetime.now(tz=TIMEZONE)
    from_date = to_date - datetime.timedelta(days=365 * 1)
    db_commands_queue = Queue()
    db_events_queue = Queue()

    processes = [
        Process(
            target=DBManager,
            kwargs={
                "db_commands_queue": db_commands_queue,
                "db_events_queue": db_events_queue,
            },
        ),
        Process(
            target=Backtest,
            kwargs={
                "asset": ASSETS["btcusdt"],
                "from_date": from_date,
                "to_date": to_date,
                "db_commands_queue": db_commands_queue,
                "db_events_queue": db_events_queue,
            },
        ),
    ]

    for process in processes:
        process.start()

    for process in processes:
        process.join()
