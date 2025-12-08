"""Backtest entry point for historical strategy simulation."""

from __future__ import annotations

import argparse
import datetime
import sys
import time
from multiprocessing import Process, Queue
from typing import Any

from configs.timezone import TIMEZONE
from helpers.get_portfolio_by_path import get_portfolio_by_path
from helpers.parse_date import parse_date
from services.authentication import AuthenticationService
from services.backtest import BacktestService
from services.commands import CommandsService
from services.logging import LoggingService


class Backtest(BacktestService):
    """Backtest process wrapper that runs historical simulation."""

    def __init__(
        self,
        **kwargs: Any,
    ) -> None:
        """Initialize and immediately start backtest execution.

        Args:
            **kwargs: Arguments passed to BacktestService.
        """
        super().__init__(**kwargs)
        super().run()


class Commands(CommandsService):
    """Commands process wrapper for backtest control."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize commands service.

        Args:
            **kwargs: Arguments passed to CommandsService.
        """
        super().__init__(**kwargs)


if __name__ == "__main__":
    authentication_service = AuthenticationService()

    if not authentication_service.setup():
        sys.exit(1)

    commands_queue: Queue[Any] = Queue()
    events_queue: Queue[Any] = Queue()

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
    restore_ticks = args.restore_ticks == "true"

    if restore_ticks:
        log = LoggingService()
        log.warning("Full data cleanup will be executed")
        log.warning("Waiting 10 seconds before deleting existing data...")
        time.sleep(10)

    from_date = parse_date(
        args.from_date,
        timezone=TIMEZONE,
        parser=parser,
        argument="--from-date",
    )

    to_date = (
        parse_date(args.to_date, timezone=TIMEZONE, parser=parser, argument="--to-date")
        if args.to_date
        else datetime.datetime.now(tz=TIMEZONE)
    )
    portfolio = get_portfolio_by_path(args.portfolio_path)

    if not portfolio.assets:
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

    for asset, allocation in portfolio.assets:
        processes.append(
            Process(
                target=Backtest,
                kwargs={
                    "asset": asset,
                    "portfolio_path": args.portfolio_path,
                    "from_date": from_date,
                    "to_date": to_date,
                    "commands_queue": commands_queue,
                    "events_queue": events_queue,
                    "allocation": allocation,
                    "args": args,
                },
            )
        )

    for process in processes:
        process.start()

    for process in processes:
        process.join()
