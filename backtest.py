"""Backtest entry point for historical strategy simulation."""

from __future__ import annotations

import argparse
import datetime
import time
import uuid
from multiprocessing import Process, Queue
from threading import Thread
from typing import Any, Dict

from vendor.configs.timezone import TIMEZONE
from vendor.enums.backtest_event import BacktestEvent
from vendor.helpers.get_portfolio_by_path import get_portfolio_by_path
from vendor.helpers.parse_date import parse_date
from vendor.interfaces.logging import LoggingInterface
from vendor.services.backtest import BacktestService
from vendor.services.commands import CommandService
from vendor.services.logging import LoggingService


class EventHandler:
    """Handles backtest events from the events queue."""

    _commands_queue: Queue[Any]
    _events_queue: Queue[Any]
    _portfolio_id: str

    _log: LoggingInterface

    def __init__(
        self,
        events_queue: Queue[Any],
        commands_queue: Queue[Any],
        portfolio_id: str,
    ) -> None:
        """Initialize the event handler."""
        self._log = LoggingService()
        self._events_queue = events_queue
        self._commands_queue = commands_queue
        self._portfolio_id = portfolio_id

    def start(self) -> None:
        """Start listening for events."""
        while True:
            event_data: Dict[str, Any] = self._events_queue.get()
            event = event_data.get("event")

            if event == BacktestEvent.BACKTEST_FINISHED:
                self._handle_finished(event_data)
                break

            if event == BacktestEvent.BACKTEST_FAILED:
                self._handle_failed(event_data)
                break

    def _handle_finished(self, event_data: Dict[str, Any]) -> None:
        report = event_data.get("report", {})
        report_path = event_data.get("report_path", "")

        self._log.info(
            "Backtest completed",
            portfolio_id=self._portfolio_id,
        )

        self._print_report(report)

        if report_path:
            self._log.info("Report files saved", path=report_path)

    def _print_report(self, report: Dict[str, Any]) -> None:
        lines = [
            "\n" + "=" * 60,
            f"  BACKTEST REPORT: {report.get('portfolio', 'N/A')}",
            "=" * 60,
            f"  Allocation:    ${report.get('allocation', 0):,.2f}",
            f"  Total Profit:  ${report.get('total_profit', 0):,.2f}",
            f"  Return:        {report.get('return_pct', 0):.2f}%",
            f"  Total Trades:  {report.get('total_trades', 0)}",
        ]

        for asset_report in report.get("assets", []):
            lines.append(f"\n  --- {asset_report.get('symbol', 'N/A')} ---")
            lines.append(f"  Allocation:  ${asset_report.get('allocation', 0):,.2f}")
            lines.append(f"  Balance:     ${asset_report.get('balance', 0):,.2f}")
            lines.append(f"  NAV:         ${asset_report.get('nav', 0):,.2f}")
            lines.append(f"  Profit:      ${asset_report.get('total_profit', 0):,.2f}")
            lines.append(f"  Return:      {asset_report.get('return_pct', 0):.2f}%")

            for strategy_report in asset_report.get("strategies", []):
                lines.append(f"\n    [{strategy_report.get('strategy_id', 'N/A')}]")
                lines.append(f"    Trades:        {strategy_report.get('total_trades', 0)}")
                wins = strategy_report.get("winning_trades", 0)
                losses = strategy_report.get("losing_trades", 0)
                lines.append(f"    Win/Loss:      {wins}/{losses}")
                lines.append(f"    Win Rate:      {strategy_report.get('win_rate', 0):.2f}%")
                lines.append(f"    Profit:        ${strategy_report.get('total_profit', 0):,.2f}")
                lines.append(f"    Gross Profit:  ${strategy_report.get('gross_profit', 0):,.2f}")
                lines.append(f"    Gross Loss:    ${strategy_report.get('gross_loss', 0):,.2f}")
                lines.append(f"    Avg Win:       ${strategy_report.get('average_win', 0):,.2f}")
                lines.append(f"    Avg Loss:      ${strategy_report.get('average_loss', 0):,.2f}")
                lines.append(f"    Profit Factor: {strategy_report.get('profit_factor', 0):.2f}")
                lines.append(f"    Cancelled:     {strategy_report.get('cancelled_trades', 0)}")

        lines.append("=" * 60 + "\n")

        self._log.info("\n".join(lines))

    def _handle_failed(self, event_data: Dict[str, Any]) -> None:
        error = event_data.get("error", "Unknown error")
        self._log.error(
            "Backtest failed",
            error=error,
        )


if __name__ == "__main__":
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

    log = LoggingService()

    backtest_id = str(uuid.uuid4())
    log.info(
        "Backtest created",
        backtest_id=backtest_id,
    )

    commands_process = Process(
        target=CommandService,
        kwargs={
            "commands_queue": commands_queue,
            "events_queue": events_queue,
        },
    )
    commands_process.start()

    event_handler = EventHandler(
        events_queue=events_queue,
        commands_queue=commands_queue,
        portfolio_id=portfolio.id,
    )

    event_thread = Thread(target=event_handler.start)
    event_thread.start()

    backtest_service = BacktestService(
        portfolio=portfolio,
        backtest_id=backtest_id,
        from_date=from_date,
        to_date=to_date,
        events_queue=events_queue,
        commands_queue=commands_queue,
        restore_ticks=restore_ticks,
    )

    backtest_service.run()

    event_thread.join()
    commands_process.join()
