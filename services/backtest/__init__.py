"""Backtest service for historical strategy simulation."""

from __future__ import annotations

import argparse
import datetime
import signal
import sys
from multiprocessing import Queue
from time import sleep
from types import FrameType
from typing import Any, Optional, Type

from configs.timezone import TIMEZONE
from enums.backtest_event import BacktestEvent
from helpers.get_duration import get_duration
from helpers.get_portfolio_by_path import get_portfolio_by_path
from interfaces.asset import AssetInterface
from interfaces.backtest import BacktestInterface
from services.logging import LoggingService
from services.ticks import TicksService


class BacktestService(BacktestInterface):
    """Backtest service for simulating trading strategies on historical data.

    Manages backtest lifecycle including setup, tick processing, and result collection.

    Attributes:
        _id: Unique backtest identifier.
        _tick: Ticks service for historical data.
        _commands_queue: Queue for inter-process commands.
        _events_queue: Queue for event broadcasting.
        _portfolio_path: Path to portfolio configuration.
    """

    _allocation: float
    _commands_queue: Optional[Queue[Any]]
    _events_queue: Queue[Any]
    _id: str
    _portfolio_path: Optional[str]
    _shutdown_requested: bool
    _tick: TicksService

    def __init__(
        self,
        asset: Type[AssetInterface],
        backtest_id: str,
        from_date: datetime.datetime,
        to_date: datetime.datetime,
        events_queue: Queue[Any],
        commands_queue: Optional[Queue[Any]] = None,
        portfolio_path: Optional[str] = None,
        allocation: float = 0.0,
        args: Optional[argparse.Namespace] = None,
    ) -> None:
        """Initialize backtest service with asset and date range.

        Args:
            asset: Asset class to backtest.
            backtest_id: Unique backtest identifier from the main process.
            from_date: Start date for backtest.
            to_date: End date for backtest.
            commands_queue: Queue for receiving commands.
            events_queue: Queue for publishing events.
            portfolio_path: Path to portfolio configuration.
            allocation: Allocation amount for this asset.
            args: Command-line arguments namespace.
        """
        restore_ticks = args.restore_ticks == "true" if args is not None else False

        self._shutdown_requested = False
        self._setup_signal_handlers()

        self._id = backtest_id
        self._start_at = datetime.datetime.now(tz=TIMEZONE)
        self._from_date = from_date
        self._to_date = to_date
        self._restore_ticks = restore_ticks
        self._portfolio_path = portfolio_path
        self._allocation = allocation
        self._commands_queue = commands_queue
        self._events_queue = events_queue

        self._log = LoggingService()
        self._log.info(f"Backtesting service started for backtest: {self._id}")

        self._asset = asset(allocation=allocation)
        self._tick = TicksService()

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

        if len(ticks) == 0:
            self._log.error("No ticks found")
            self._send_failed("No ticks found")
            return

        if enabled_strategies == 0:
            self._log.error("No enabled strategies found")
            self._send_failed("No enabled strategies found")
            return

        for tick_model in ticks:
            self._asset.on_tick(tick_model)

        self._on_end()

    def _handle_shutdown(
        self,
        _signum: int,
        _frame: Optional[FrameType],
    ) -> None:
        if self._shutdown_requested:
            return

        self._shutdown_requested = True
        self._log.info("Shutdown signal received, cleaning up...")
        self._send_failed("Shutdown signal received")

        sleep(3)
        sys.exit(0)

    def _on_end(self) -> None:
        end_at = datetime.datetime.now(TIMEZONE)
        duration = get_duration(self._start_at, end_at)
        report = self._asset.on_end()

        self._events_queue.put(
            {
                "event": BacktestEvent.BACKTEST_FINISHED,
                "asset_id": self._asset.symbol,
                "report": report,
            }
        )

        self._log.info(f"Backtest completed in: {duration}")

    def _send_failed(self, error: str) -> None:
        self._events_queue.put(
            {
                "event": BacktestEvent.BACKTEST_FAILED,
                "asset_id": self._asset.symbol,
                "error": error,
            }
        )

    def _setup_signal_handlers(self) -> None:
        signal.signal(
            signal.SIGINT,
            self._handle_shutdown,
        )

        signal.signal(
            signal.SIGTERM,
            self._handle_shutdown,
        )
