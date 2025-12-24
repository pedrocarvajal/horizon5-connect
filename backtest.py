"""Backtest entry point for historical strategy simulation."""

from __future__ import annotations

import argparse
import datetime
import sys
import time
from multiprocessing import Process, Queue
from threading import Thread
from typing import Any, Dict, List, Optional

from vendor.configs.timezone import TIMEZONE
from vendor.enums.backtest_event import BacktestEvent
from vendor.enums.backtest_status import BacktestStatus
from vendor.helpers.get_portfolio_by_path import get_portfolio_by_path
from vendor.helpers.parse_date import parse_date
from vendor.interfaces.logging import LoggingInterface
from vendor.interfaces.portfolio import PortfolioInterface
from vendor.models.backtest_settings import (
    AssetSettingsModel,
    BacktestSettingsModel,
    PortfolioSettingsModel,
    StrategySettingsModel,
)
from vendor.providers.horizon_router import HorizonRouterProvider
from vendor.services.authentication import AuthenticationService
from vendor.services.backtest import BacktestService
from vendor.services.commands import CommandService
from vendor.services.logging import LoggingService


class EventHandler:
    """Handles backtest events from the events queue."""

    _backtest_id: str
    _commands_queue: Queue[Any]
    _events_queue: Queue[Any]
    _portfolio_id: str

    _horizon_router: HorizonRouterProvider
    _log: LoggingInterface

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

    def _handle_finished(self, event_data: Dict[str, Any]) -> None:
        report = event_data.get("report", {})
        report["portfolio_id"] = self._portfolio_id

        self._log.info(
            "Backtest completed",
            portfolio_id=self._portfolio_id,
        )
        self._log.debug(report)

        self._horizon_router.backtest_update(
            backtest_id=self._backtest_id,
            status=BacktestStatus.COMPLETED.value,
            analytics=report,
        )

    def _handle_failed(self, event_data: Dict[str, Any]) -> None:
        error = event_data.get("error", "Unknown error")
        self._log.error(
            "Backtest failed",
            error=error,
        )

        self._horizon_router.backtest_update(
            backtest_id=self._backtest_id,
            status=BacktestStatus.FAILED.value,
            analytics={"error": error},
        )


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

    for asset in portfolio.assets:
        strategy_settings_list: List[StrategySettingsModel] = []

        for strategy in asset.strategies:
            strategy_settings = getattr(strategy, "_settings", {})
            strategy_settings_list.append(
                StrategySettingsModel(
                    id=strategy.id,
                    allocation=strategy.allocation,
                    leverage=asset.leverage,
                    settings=strategy_settings,
                )
            )

        asset_settings_list.append(
            AssetSettingsModel(
                symbol=asset.symbol,
                gateway=getattr(asset, "_gateway_name", ""),
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
        log.info(
            "Backtest created",
            backtest_id=backtest_id,
        )

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
