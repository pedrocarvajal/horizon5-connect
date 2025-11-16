import argparse
import datetime
from multiprocessing import Process, Queue
from typing import Any

from configs.timezone import TIMEZONE
from helpers.get_portfolio_by_path import get_portfolio_by_path
from services.backtest import BacktestService
from services.commands import CommandsService


class Backtest(BacktestService):
    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(
        self,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        super().run()


class Commands(CommandsService):
    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)


def _parse_date(
    value: str,
    parser: argparse.ArgumentParser,
    argument: str,
) -> datetime.datetime:
    try:
        return datetime.datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=TIMEZONE)
    except ValueError:
        parser.error(f"Invalid value for {argument}. Use YYYY-MM-DD (e.g. 2024-01-31).")


if __name__ == "__main__":
    commands_queue = Queue()
    events_queue = Queue()

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--portfolio-path",
        required=True,
    )

    parser.add_argument(
        "--from-date",
        required=True,
    )

    parser.add_argument(
        "--to-date",
        required=False,
    )

    parser.add_argument(
        "--restore-ticks",
        required=False,
        choices=["true", "false"],
        default="false",
    )

    args = parser.parse_args()

    from_date = _parse_date(
        args.from_date,
        parser,
        "--from-date",
    )

    to_date = (
        _parse_date(args.to_date, parser, "--to-date")
        if args.to_date
        else datetime.datetime.now(tz=TIMEZONE)
    )

    portfolio = get_portfolio_by_path(args.portfolio_path)
    assets = getattr(portfolio, "assets", None)

    if assets is None:
        assets = getattr(portfolio, "_assets", None)

    if not assets:
        parser.error("Portfolio must define at least one asset.")

    processes = [
        Process(
            target=Commands,
            kwargs={
                "commands_queue": commands_queue,
                "events_queue": events_queue,
            },
        ),
    ]

    for asset in assets:
        processes.append(
            Process(
                target=Backtest,
                kwargs={
                    "asset": asset,
                    "from_date": from_date,
                    "to_date": to_date,
                    "commands_queue": commands_queue,
                    "events_queue": events_queue,
                    "args": args,
                },
            )
        )

    for process in processes:
        process.start()

    for process in processes:
        process.join()
