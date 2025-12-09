"""Backtest entry point for historical strategy simulation."""

from __future__ import annotations

import argparse
import datetime
import select
import sys
import termios
import time
import tty
from multiprocessing import Process, Queue
from threading import Thread
from typing import Any, Dict, List, Optional

from configs.timezone import TIMEZONE
from enums.backtest_event import BacktestEvent
from enums.backtest_status import BacktestStatus
from enums.command import Command
from helpers.get_portfolio_by_path import get_portfolio_by_path
from helpers.parse_date import parse_date
from interfaces.portfolio import PortfolioInterface
from models.backtest_settings import (
    AssetSettingsModel,
    BacktestSettingsModel,
    PortfolioSettingsModel,
    StrategySettingsModel,
)
from providers.horizon_router import HorizonRouterProvider
from services.authentication import AuthenticationService
from services.backtest import BacktestService
from services.commands import CommandService
from services.logging import LoggingService


class EventHandler:
    """Handles backtest events from the events queue."""

    _backtest_id: str
    _commands_queue: Queue[Any]
    _events_queue: Queue[Any]
    _portfolio_id: str

    _horizon_router: HorizonRouterProvider
    _log: LoggingService

    def __init__(
        self,
        events_queue: Queue[Any],
        commands_queue: Queue[Any],
        portfolio_id: str,
        backtest_id: str,
    ) -> None:
        """Initialize the event handler."""
        self._log = LoggingService()
        self._events_queue = events_queue
        self._commands_queue = commands_queue
        self._portfolio_id = portfolio_id
        self._backtest_id = backtest_id
        self._horizon_router = HorizonRouterProvider()

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

        self._commands_queue.put({"command": Command.KILL})

    def _handle_finished(self, event_data: Dict[str, Any]) -> None:
        report = event_data.get("report", {})
        report["portfolio_id"] = self._portfolio_id

        self._log.info(f"Portfolio ID: {self._portfolio_id}")
        self._log.debug(report)

        self._horizon_router.backtest_update(
            backtest_id=self._backtest_id,
            status=BacktestStatus.COMPLETED.value,
            analytics=report,
        )

    def _handle_failed(self, event_data: Dict[str, Any]) -> None:
        error = event_data.get("error", "Unknown error")
        self._log.error(f"Backtest failed: {error}")

        self._horizon_router.backtest_update(
            backtest_id=self._backtest_id,
            status=BacktestStatus.FAILED.value,
            analytics={"error": error},
        )


class KeyboardListener:
    """Listens for Esc key press to trigger shutdown."""

    _commands_queue: Queue[Any]
    _running: bool
    _log: LoggingService

    def __init__(self, commands_queue: Queue[Any]) -> None:
        """Initialize keyboard listener."""
        self._commands_queue = commands_queue
        self._running = True
        self._log = LoggingService()

    def start(self) -> None:
        """Listen for Esc key (char code 27) in a loop with timeout."""
        if not sys.stdin.isatty():
            return

        old_settings = termios.tcgetattr(sys.stdin)

        try:
            tty.setcbreak(sys.stdin.fileno())

            while self._running:
                ready, _, _ = select.select([sys.stdin], [], [], 0.5)

                if not ready:
                    continue

                char = sys.stdin.read(1)

                if char == "\x1b":
                    self._log.info("Esc pressed - sending kill signal...")
                    self._commands_queue.put({"command": Command.KILL})
                    self._running = False
                    break

        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

    def stop(self) -> None:
        """Stop the keyboard listener."""
        self._running = False


def create_backtest(
    portfolio_path: str,
    portfolio: PortfolioInterface,
    from_date: datetime.datetime,
    to_date: datetime.datetime,
) -> Optional[str]:
    """Create a backtest in the backend and return the backtest_id."""
    log = LoggingService()
    horizon_router = HorizonRouterProvider()
    asset_settings_list: List[AssetSettingsModel] = []

    for asset_class, allocation in portfolio.assets:
        asset_instance = asset_class(allocation=allocation)

        if not asset_instance.enabled:
            continue

        strategy_settings_list: List[StrategySettingsModel] = []

        for strategy in asset_instance.strategies:
            strategy_settings = getattr(strategy, "_settings", {})
            strategy_settings_list.append(
                StrategySettingsModel(
                    id=strategy.id,
                    enabled=strategy.enabled,
                    allocation=getattr(strategy, "_allocation", 0.0),
                    leverage=getattr(strategy, "_leverage", 1),
                    settings=strategy_settings,
                )
            )

        asset_settings_list.append(
            AssetSettingsModel(
                symbol=asset_instance.symbol,
                gateway=getattr(asset_instance, "_gateway_name", ""),
                strategies=strategy_settings_list,
            )
        )

    portfolio_settings = PortfolioSettingsModel(
        id=portfolio.id,
        path=portfolio_path,
    )

    settings = BacktestSettingsModel(
        from_date=int(from_date.timestamp()),
        to_date=int(to_date.timestamp()),
        portfolio=portfolio_settings,
        assets=asset_settings_list,
    )

    response = horizon_router.backtest_create(settings=settings.to_dict())
    backtest_id: Optional[str] = response.get("data", {}).get("id")

    if backtest_id:
        log.info(f"Backtest created: {backtest_id}")

    return backtest_id


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

    log = LoggingService()

    has_enabled_assets = False
    for asset_class, allocation in portfolio.assets:
        instance = asset_class(allocation=allocation)
        if instance.enabled:
            has_enabled_assets = True
        else:
            log.warning(f"Asset {instance.symbol} is not enabled")

    if not has_enabled_assets:
        parser.error("No enabled assets found in portfolio.")

    backtest_id = create_backtest(
        portfolio_path=args.portfolio_path,
        portfolio=portfolio,
        from_date=from_date,
        to_date=to_date,
    )

    if not backtest_id:
        log.error("Failed to create backtest")
        sys.exit(1)

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
        backtest_id=backtest_id,
    )

    event_thread = Thread(target=event_handler.start)
    event_thread.start()

    keyboard_listener = KeyboardListener(commands_queue=commands_queue)
    keyboard_thread = Thread(target=keyboard_listener.start, daemon=True)
    keyboard_thread.start()

    log.info("Press Esc to stop the backtest")

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

    keyboard_listener.stop()
    event_thread.join()
    commands_process.join()
