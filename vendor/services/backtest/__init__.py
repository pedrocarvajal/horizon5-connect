"""Backtest service for historical strategy simulation."""

from __future__ import annotations

import datetime
from multiprocessing import Queue
from typing import Any, List, Optional

from vendor.configs.timezone import TIMEZONE
from vendor.enums.backtest_event import BacktestEvent
from vendor.enums.command import Command
from vendor.helpers.get_duration import get_duration
from vendor.interfaces.backtest import BacktestInterface
from vendor.interfaces.logging import LoggingInterface
from vendor.interfaces.portfolio import PortfolioInterface
from vendor.interfaces.ticks import TicksInterface
from vendor.services.backtest.report import generate_report
from vendor.services.logging import LoggingService
from vendor.services.ticks import DownloadTask, TicksService


class BacktestService(BacktestInterface):
    """Backtest service for simulating trading strategies on historical data."""

    _commands_queue: Optional[Queue[Any]]
    _events_queue: Queue[Any]

    _id: str
    _from_date: datetime.datetime
    _to_date: datetime.datetime
    _start_at: datetime.datetime
    _should_restore_ticks: bool

    _portfolio: PortfolioInterface
    _log: LoggingInterface
    _ticks_service: TicksInterface

    def __init__(
        self,
        portfolio: PortfolioInterface,
        backtest_id: str,
        from_date: datetime.datetime,
        to_date: datetime.datetime,
        events_queue: Queue[Any],
        commands_queue: Optional[Queue[Any]] = None,
        restore_ticks: bool = False,
    ) -> None:
        """Initialize backtest service with portfolio and date range."""
        self._id = backtest_id
        self._from_date = from_date
        self._to_date = to_date
        self._should_restore_ticks = restore_ticks
        self._commands_queue = commands_queue
        self._events_queue = events_queue

        self._start_at = datetime.datetime.now(tz=TIMEZONE)

        self._log = LoggingService()
        self._ticks_service = TicksService()

        self._log.info(
            "Backtesting service started",
            backtest_id=self._id,
        )

        self.setup(
            portfolio=portfolio,
        )

    def run(self) -> None:
        """Execute backtest by iterating timeline and feeding ticks to portfolio."""
        assets = self._portfolio.assets

        if not assets:
            self._log.error("No enabled assets found")
            self._send_failed("No enabled assets found")
            return

        symbols = [asset.symbol for asset in assets]
        timeline = self._ticks_service.get_timeline(self._from_date, self._to_date)
        total_ticks = len(timeline)

        if total_ticks == 0:
            self._log.error("No timeline generated")
            self._send_failed("No timeline generated")
            return

        self._log.info(
            "Processing ticks",
            total_ticks=f"{total_ticks:,}",
            assets_count=len(assets),
        )

        ticks_iterator = self._ticks_service.iterate_ticks(
            symbols=symbols,
            from_date=self._from_date,
            to_date=self._to_date,
        )

        for index, (_tick_date, ticks) in enumerate(ticks_iterator):
            if ticks:
                self._portfolio.on_tick(ticks)

            if (index + 1) % 100000 == 0:
                progress = ((index + 1) / total_ticks) * 100

                self._log.info(
                    "Backtest progress",
                    progress=f"{progress:.1f}%",
                    current=f"{index + 1:,}",
                    total=f"{total_ticks:,}",
                )

        self._on_end()

    def _on_end(self) -> None:
        end_at = datetime.datetime.now(TIMEZONE)
        duration = get_duration(self._start_at, end_at)
        report = self._portfolio.on_end()

        trade_histories = report.pop("trade_histories", {})
        for asset_report in report.get("assets", []):
            asset_report.pop("trade_histories", None)

        report_path = generate_report(
            backtest_id=self._id,
            report=report,
            trade_histories=trade_histories,
            allocation=report.get("allocation", 0),
        )

        self._log.info("Report saved", path=str(report_path))

        self._events_queue.put(
            {
                "event": BacktestEvent.BACKTEST_FINISHED,
                "portfolio_id": self._portfolio.id,
                "report": report,
                "report_path": str(report_path),
            }
        )

        self._send_shutdown()

        self._log.info(
            "Backtest completed",
            duration=duration,
        )

    def _send_failed(self, error: str) -> None:
        self._events_queue.put(
            {
                "event": BacktestEvent.BACKTEST_FAILED,
                "portfolio_id": self._portfolio.id,
                "error": error,
            }
        )

        self._send_shutdown()

    def _send_shutdown(self) -> None:
        if not self._commands_queue:
            return

        self._commands_queue.put({"command": Command.SHUTDOWN})

    def setup(self, portfolio: PortfolioInterface) -> None:
        """Configure portfolio and download tick data for all assets in parallel."""
        self._portfolio = portfolio
        self._portfolio.setup(
            backtest=True,
            backtest_id=self._id,
            commands_queue=self._commands_queue,
            events_queue=self._events_queue,
        )

        download_tasks: List[DownloadTask] = [
            DownloadTask(asset=asset, restore_ticks=self._should_restore_ticks) for asset in self._portfolio.assets
        ]

        if not download_tasks:
            return

        def _on_download_complete(symbol: str) -> None:
            self._log.info(
                "Tick data ready",
                symbol=symbol,
            )

        def _on_all_downloads_complete() -> None:
            self._log.info("All tick data downloads completed")

        TicksService.download_parallel(
            tasks=download_tasks,
            on_complete=_on_download_complete,
            on_all_complete=_on_all_downloads_complete,
        )
