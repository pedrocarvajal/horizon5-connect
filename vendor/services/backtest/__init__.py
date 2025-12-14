"""Backtest service for historical strategy simulation."""

from __future__ import annotations

import datetime
from multiprocessing import Queue
from typing import Any, List, Optional

from vendor.configs.timezone import TIMEZONE
from vendor.enums.backtest_event import BacktestEvent
from vendor.helpers.get_duration import get_duration
from vendor.interfaces.asset import AssetInterface
from vendor.interfaces.backtest import BacktestInterface
from vendor.interfaces.portfolio import PortfolioInterface
from vendor.services.logging import LoggingService
from vendor.services.ticks import DownloadTask, TicksService


class BacktestService(BacktestInterface):
    """Backtest service for simulating trading strategies on historical data."""

    _commands_queue: Optional[Queue[Any]]
    _events_queue: Queue[Any]
    _from_date: datetime.datetime
    _id: str
    _portfolio: PortfolioInterface
    _should_restore_ticks: bool
    _start_at: datetime.datetime
    _to_date: datetime.datetime

    _log: LoggingService
    _ticks_service: TicksService

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
        self._start_at = datetime.datetime.now(tz=TIMEZONE)
        self._from_date = from_date
        self._to_date = to_date
        self._should_restore_ticks = restore_ticks
        self._commands_queue = commands_queue
        self._events_queue = events_queue
        self._portfolio = portfolio

        self._log = LoggingService()
        self._ticks_service = TicksService()
        self._log.info(f"Backtesting service started for backtest: {self._id}")

        self._setup_portfolio()

    def run(self) -> None:
        """Execute backtest by iterating timeline and feeding ticks to portfolio."""
        assets = self._portfolio.asset_instances

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

        self._log.info(f"Processing {total_ticks:,} ticks for {len(assets)} assets")

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
                self._log.info(f"Progress: {progress:.1f}% ({index + 1:,}/{total_ticks:,})")

        self._on_end()

    def _on_end(self) -> None:
        end_at = datetime.datetime.now(TIMEZONE)
        duration = get_duration(self._start_at, end_at)
        report = self._portfolio.on_end()

        self._events_queue.put(
            {
                "event": BacktestEvent.BACKTEST_FINISHED,
                "portfolio_id": self._portfolio.id,
                "report": report,
            }
        )

        self._log.info(f"Backtest completed in: {duration}")

    def _send_failed(self, error: str) -> None:
        self._events_queue.put(
            {
                "event": BacktestEvent.BACKTEST_FAILED,
                "portfolio_id": self._portfolio.id,
                "error": error,
            }
        )

    def _setup_portfolio(self) -> None:
        """Configure portfolio and download tick data for all assets in parallel."""
        setup_kwargs = {
            "backtest": True,
            "backtest_id": self._id,
            "commands_queue": self._commands_queue,
            "events_queue": self._events_queue,
            "portfolio": self._portfolio,
        }

        enabled_asset_instances: List[AssetInterface] = []
        download_tasks: List[DownloadTask] = []

        for asset_config in self._portfolio.assets:
            asset_class = asset_config["asset"]
            allocation = asset_config["allocation"]
            enabled = asset_config.get("enabled", True)

            if not enabled:
                self._log.warning(f"Asset {asset_class.__name__} is disabled in portfolio config")
                continue

            asset_instance = asset_class(allocation=allocation, enabled=enabled)
            enabled_asset_instances.append(asset_instance)
            download_tasks.append(
                DownloadTask(
                    asset=asset_instance,
                    restore_ticks=self._should_restore_ticks,
                )
            )

        if not download_tasks:
            return

        def _on_download_complete(symbol: str) -> None:
            self._log.info(f"Tick data ready for {symbol}")

        def _on_all_downloads_complete() -> None:
            self._log.info("All tick data downloads completed, proceeding with backtest setup")

        tick_services_by_symbol = TicksService.download_parallel(
            tasks=download_tasks,
            on_complete=_on_download_complete,
            on_all_complete=_on_all_downloads_complete,
        )

        for asset_instance in enabled_asset_instances:
            tick_service = tick_services_by_symbol.get(asset_instance.symbol)

            if tick_service is None:
                self._log.error(f"No tick service for {asset_instance.symbol}")
                continue

            asset_instance.setup(
                tick=tick_service,
                asset=asset_instance,
                **setup_kwargs,
            )

            self._portfolio.asset_instances.append(asset_instance)

        self._portfolio.setup_analytic(**setup_kwargs)
