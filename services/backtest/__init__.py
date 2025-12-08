"""Backtest service for historical strategy simulation."""

from __future__ import annotations

import argparse
import datetime
import signal
import sys
from multiprocessing import Queue
from time import sleep
from types import FrameType
from typing import Any, Dict, List, Optional, Type

from configs.timezone import TIMEZONE
from enums.backtest_status import BacktestStatus
from enums.command import Command
from helpers.get_duration import get_duration
from helpers.get_portfolio_by_path import get_portfolio_by_path
from interfaces.asset import AssetInterface
from interfaces.backtest import BacktestInterface
from models.backtest_settings import (
    AssetSettingsModel,
    BacktestSettingsModel,
    PortfolioSettingsModel,
    StrategySettingsModel,
)
from providers.horizon_router import HorizonRouterProvider
from services.logging import LoggingService
from services.ticks import TicksService


class BacktestService(BacktestInterface):
    """Backtest service for simulating trading strategies on historical data.

    Manages backtest lifecycle including setup, tick processing, and result collection.
    Integrates with HorizonRouter API for backtest tracking and analytics.

    Attributes:
        _id: Unique backtest identifier.
        _tick: Ticks service for historical data.
        _commands_queue: Queue for inter-process commands.
        _events_queue: Queue for event broadcasting.
        _horizon_router: Provider for HorizonRouter API.
        _portfolio_path: Path to portfolio configuration.
    """

    _id: Optional[str]
    _tick: TicksService
    _commands_queue: Optional[Queue[Any]]
    _events_queue: Optional[Queue[Any]]
    _horizon_router: HorizonRouterProvider
    _portfolio_path: Optional[str]
    _shutdown_requested: bool

    def __init__(
        self,
        asset: Type[AssetInterface],
        from_date: datetime.datetime,
        to_date: datetime.datetime,
        commands_queue: Optional[Queue[Any]] = None,
        events_queue: Optional[Queue[Any]] = None,
        portfolio_path: Optional[str] = None,
        args: Optional[argparse.Namespace] = None,
    ) -> None:
        """Initialize backtest service with asset and date range.

        Args:
            asset: Asset class to backtest.
            from_date: Start date for backtest.
            to_date: End date for backtest.
            commands_queue: Queue for receiving commands.
            events_queue: Queue for publishing events.
            portfolio_path: Path to portfolio configuration.
            args: Command-line arguments namespace.
        """
        restore_ticks = args.restore_ticks == "true" if args is not None else False

        self._shutdown_requested = False
        self._setup_signal_handlers()

        self._id = None
        self._start_at = datetime.datetime.now(tz=TIMEZONE)
        self._from_date = from_date
        self._to_date = to_date
        self._restore_ticks = restore_ticks
        self._portfolio_path = portfolio_path
        self._commands_queue = commands_queue
        self._events_queue = events_queue

        self._log = LoggingService()
        self._log.info("Backtesting service started")

        self._asset = asset()
        self._tick = TicksService()
        self._horizon_router = HorizonRouterProvider()

        self._create_backtest()

        tick_setup = {
            "restore_ticks": restore_ticks,
        }

        instances = {
            "tick": self._tick,
            "asset": self._asset,
        }

        queues = {
            "commands_queue": commands_queue,
            "events_queue": events_queue,
        }

        self._tick.setup(
            **instances,
            **tick_setup,
        )

        portfolio = None

        if portfolio_path:
            portfolio = get_portfolio_by_path(portfolio_path)

        self._asset.setup(
            backtest=True,
            backtest_id=self._id,
            portfolio=portfolio,
            **instances,
            **queues,
        )

    def run(self) -> None:
        """Execute backtest by processing all ticks in date range."""
        enabled_strategies = len(self._asset.strategies)
        ticks = self._tick.ticks(
            from_date=self._from_date,
            to_date=self._to_date,
        )

        if not self._id:
            self._log.error("Failed to create backtest...")
            self._kill()
            return

        if len(ticks) == 0:
            self._log.error("No ticks found")
            self._kill()
            return

        if enabled_strategies == 0:
            self._log.error("No enabled strategies found")
            self._kill()
            return

        for tick_model in ticks:
            self._asset.on_tick(tick_model)

        self._on_end()

    def _create_backtest(self) -> None:
        portfolio_id = ""
        strategies: List[StrategySettingsModel] = []

        if self._portfolio_path:
            portfolio_instance = get_portfolio_by_path(self._portfolio_path)

            if portfolio_instance:
                portfolio_id = portfolio_instance.id

        for strategy in self._asset.strategies:
            strategy_settings = getattr(strategy, "_settings", {})
            strategies.append(
                StrategySettingsModel(
                    id=strategy.id,
                    enabled=strategy.enabled,
                    allocation=getattr(strategy, "_allocation", 0.0),
                    leverage=getattr(strategy, "_leverage", 1),
                    settings=strategy_settings,
                )
            )

        asset = AssetSettingsModel(
            symbol=self._asset.symbol,
            gateway=getattr(self._asset, "_gateway_name", ""),
        )

        portfolio = PortfolioSettingsModel(
            id=portfolio_id,
            path=self._portfolio_path or "",
        )

        settings = BacktestSettingsModel(
            from_date=int(self._from_date.timestamp()),
            to_date=int(self._to_date.timestamp()),
            portfolio=portfolio,
            asset=asset,
            strategies=strategies,
        )

        response = self._horizon_router.backtest_create(
            settings=settings.to_dict(),
        )

        self._id = response["data"]["id"]
        self._log.info(f"Backtest created: {self._id}")

    def _handle_shutdown(
        self,
        _signum: int,
        _frame: Optional[FrameType],
    ) -> None:
        if self._shutdown_requested:
            return

        self._shutdown_requested = True
        self._log.info("Shutdown signal received, cleaning up...")
        self._kill()

        sleep(3)
        sys.exit(0)

    def _kill(self) -> None:
        if self._commands_queue is not None:
            self._commands_queue.put(
                {
                    "command": Command.KILL,
                }
            )

    def _on_end(self) -> None:
        end_at = datetime.datetime.now(TIMEZONE)
        duration = get_duration(self._start_at, end_at)

        report = self._asset.on_end()
        self._update_backtest(status=BacktestStatus.COMPLETED.value, report=report)
        self._kill()

        self._log.info(f"Backtest completed in: {duration}")

    def _setup_signal_handlers(self) -> None:
        signal.signal(
            signal.SIGINT,
            self._handle_shutdown,
        )

        signal.signal(
            signal.SIGTERM,
            self._handle_shutdown,
        )

    def _update_backtest(
        self,
        status: str,
        report: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not self._id:
            return

        settings: Optional[Dict[str, Any]] = None

        if report is not None:
            settings = {"report": report}

        self._horizon_router.backtest_update(
            backtest_id=self._id,
            status=status,
            settings=settings,
        )
