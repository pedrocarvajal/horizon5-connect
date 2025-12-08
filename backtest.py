"""Backtest entry point for historical strategy simulation."""

from __future__ import annotations

import argparse
import datetime
import sys
import time
from multiprocessing import Process, Queue
from typing import Any, Dict

from configs.timezone import TIMEZONE
from enums.backtest_event import BacktestEvent
from enums.command import Command
from helpers.get_portfolio_by_path import get_portfolio_by_path
from helpers.parse_date import parse_date
from services.authentication import AuthenticationService
from services.backtest import BacktestService
from services.commands import CommandsService
from services.logging import LoggingService
from services.quality_calculator import QualityCalculatorService


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


class PortfolioAggregator:
    """Aggregates asset reports into a portfolio report."""

    _events_queue: Queue[Any]
    _commands_queue: Queue[Any]
    _total_assets: int
    _completed_assets: int
    _failed_assets: int
    _portfolio_id: str
    _quality_calculator: QualityCalculatorService
    _log: LoggingService

    def __init__(
        self,
        events_queue: Queue[Any],
        commands_queue: Queue[Any],
        total_assets: int,
        portfolio_id: str,
    ) -> None:
        """Initialize the portfolio aggregator."""
        self._log = LoggingService()
        self._log.info("Portfolio aggregator started")

        self._events_queue = events_queue
        self._commands_queue = commands_queue
        self._total_assets = total_assets
        self._portfolio_id = portfolio_id
        self._completed_assets = 0
        self._failed_assets = 0
        self._quality_calculator = QualityCalculatorService(children_key="assets")

        self._start()

    def _start(self) -> None:
        while True:
            event_data: Dict[str, Any] = self._events_queue.get()
            event = event_data.get("event")
            should_exit = False

            if event == BacktestEvent.BACKTEST_FINISHED:
                should_exit = self._handle_backtest_finished(event_data)
            elif event == BacktestEvent.BACKTEST_FAILED:
                should_exit = self._handle_backtest_failed(event_data)

            if should_exit:
                break

    def _handle_backtest_finished(self, event_data: Dict[str, Any]) -> bool:
        asset_id = event_data.get("asset_id")
        report = event_data.get("report")

        if asset_id is None or report is None:
            self._log.error("Asset ID or report missing in BACKTEST_FINISHED event")
            return False

        self._quality_calculator.on_report(asset_id, report)
        self._completed_assets += 1

        self._log.info(f"Asset {asset_id} completed ({self._completed_assets}/{self._total_assets})")

        return self._check_all_finished()

    def _handle_backtest_failed(self, event_data: Dict[str, Any]) -> bool:
        asset_id = event_data.get("asset_id")
        error = event_data.get("error")

        self._failed_assets += 1
        self._log.error(f"Asset {asset_id} failed: {error}")

        return self._check_all_finished()

    def _check_all_finished(self) -> bool:
        total_processed = self._completed_assets + self._failed_assets

        if total_processed >= self._total_assets:
            if self._completed_assets > 0:
                self._generate_portfolio_report()

            self._send_kill()
            return True

        return False

    def _generate_portfolio_report(self) -> None:
        portfolio_report = self._quality_calculator.on_end()
        portfolio_report["portfolio_id"] = self._portfolio_id

        self._log.info(f"Portfolio ID: {self._portfolio_id}")
        self._log.debug(portfolio_report)

    def _send_kill(self) -> None:
        self._commands_queue.put({"command": Command.KILL})


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
        Process(
            target=PortfolioAggregator,
            kwargs={
                "events_queue": events_queue,
                "commands_queue": commands_queue,
                "total_assets": len(portfolio.assets),
                "portfolio_id": portfolio.id,
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
