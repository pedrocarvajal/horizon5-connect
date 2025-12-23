"""Production service for live trading execution."""

import asyncio
import datetime
from multiprocessing import Queue
from typing import Any, List, Optional

from vendor.configs.timezone import TIMEZONE
from vendor.enums.command import Command
from vendor.helpers.get_portfolio_by_path import get_portfolio_by_path
from vendor.interfaces.asset import AssetInterface
from vendor.interfaces.portfolio import PortfolioInterface
from vendor.interfaces.production import ProductionInterface
from vendor.models.tick import TickModel
from vendor.services.logging import LoggingService
from vendor.services.ticks import TicksService


class ProductionService(ProductionInterface):
    """Service for live trading execution and stream management."""

    STREAM_TIMEOUT_SECONDS: int = 10
    HISTORICAL_DATA_DAYS: int = 365

    _assets: List[AssetInterface]
    _commands_queue: Optional["Queue[Command]"] = None
    _events_queue: Optional["Queue[Any]"] = None
    _portfolio: Optional[PortfolioInterface] = None
    _portfolio_path: Optional[str] = None
    _stream_last_updated_at: datetime.datetime
    _stream_started_at: datetime.datetime
    _stream_tasks: List[asyncio.Task[None]]

    _log: LoggingService

    def __init__(self) -> None:
        """Initialize production service."""
        self._log = LoggingService()

        self._assets = []
        self._commands_queue = None
        self._events_queue = None
        self._portfolio = None
        self._portfolio_path = None
        self._stream_started_at = datetime.datetime.now(tz=TIMEZONE)
        self._stream_last_updated_at = datetime.datetime.now(tz=TIMEZONE)
        self._stream_tasks = []

    def setup(self, **kwargs: Any) -> None:
        """Configure production service and load portfolio.

        Args:
            **kwargs: Configuration parameters including:
                commands_queue: Queue for commands (required).
                events_queue: Queue for events (required).
                portfolio_path: Path to portfolio module (required).
        """
        commands_queue = kwargs.get("commands_queue")
        events_queue = kwargs.get("events_queue")
        portfolio_path = kwargs.get("portfolio_path")

        if commands_queue is None:
            raise ValueError("Commands queue is required")

        if events_queue is None:
            raise ValueError("Events queue is required")

        if not portfolio_path:
            raise ValueError("Portfolio path is required")

        self._commands_queue = commands_queue
        self._events_queue = events_queue
        self._portfolio_path = portfolio_path
        self._load_portfolio()

    def _load_portfolio(self) -> None:
        """Load and validate the portfolio from path."""
        if not self._portfolio_path:
            raise ValueError("Portfolio path is required")

        self._portfolio = get_portfolio_by_path(self._portfolio_path)

        if not self._portfolio:
            raise ValueError("Portfolio not found")

    def run(self) -> None:
        """Start live trading execution with stream connections."""
        if not self._portfolio or not self._commands_queue or not self._events_queue:
            raise ValueError("Service not properly setup")

        for asset_config in self._portfolio.assets:
            asset_class = asset_config["asset"]
            allocation = asset_config["allocation"]
            enabled = asset_config.get("enabled", True)

            if not enabled:
                self._log.warning(
                    "Asset is disabled in portfolio config",
                    asset=asset_class.__name__,
                )
                continue

            asset_instance = asset_class(allocation=allocation, enabled=enabled)
            self._assets.append(asset_instance)

        if not self._assets:
            raise ValueError("No enabled assets found in portfolio")

        for asset in self._assets:
            asset.setup(
                asset=asset,
                backtest=False,
                backtest_id=None,
                portfolio=self._portfolio,
                commands_queue=self._commands_queue,
                events_queue=self._events_queue,
            )

        self._log.info("Collecting historical data")
        self._collect_historical()

        self._log.info("Connecting to the streams")
        asyncio.run(self._run_tasks())

    def _collect_historical(self) -> None:
        for asset in self._assets:
            tick_service = TicksService()
            tick_service.setup(
                asset=asset,
                restore_ticks=False,
                disable_download=False,
            )

            to_date = datetime.datetime.now(tz=TIMEZONE)
            from_date = to_date - datetime.timedelta(days=self.HISTORICAL_DATA_DAYS)

            self._log.info(
                "Collecting historical data",
                symbol=asset.symbol,
                from_date=str(from_date),
                to_date=str(to_date),
            )

            ticks = tick_service.ticks(
                from_date=from_date,
                to_date=to_date,
            )

            self._log.info(
                "Injecting ticks",
                symbol=asset.symbol,
                count=len(ticks),
            )

            asset.start_historical_filling()

            for tick in ticks:
                asset.on_tick(tick)

            asset.stop_historical_filling()

    async def _connect(self) -> None:
        while True:
            self._stream_tasks = []

            for asset in self._assets:
                self._stream_tasks.append(
                    asyncio.create_task(
                        self._connect_gateway_stream(asset),
                    )
                )

            try:
                await asyncio.gather(*self._stream_tasks)
            except asyncio.CancelledError:
                self._log.info("Stream tasks cancelled, reconnecting...")
                self._stream_last_updated_at = datetime.datetime.now(tz=TIMEZONE)
                await asyncio.sleep(1)
                continue

    async def _connect_gateway_stream(
        self,
        asset: AssetInterface,
    ) -> None:
        gateway = asset.gateway
        self._stream_started_at = datetime.datetime.now(tz=TIMEZONE)

        async def callback(tick: TickModel) -> None:
            self._stream_last_updated_at = tick.date
            asset.on_tick(tick)

        try:
            await gateway.stream(
                streams=[f"{asset.symbol.lower()}@bookTicker"],
                callback=callback,
            )
        except Exception as e:
            self._log.error(
                "Error connecting to gateway stream",
                asset=asset.symbol,
                error=str(e),
            )

    async def _run_tasks(self) -> None:
        await asyncio.gather(
            self._connect(),
            self._supervisor(),
        )

    async def _supervisor(self) -> None:
        while True:
            await asyncio.sleep(self.STREAM_TIMEOUT_SECONDS)

            stream_last_updated_at = self._stream_last_updated_at
            stream_time_diff = datetime.datetime.now(tz=TIMEZONE) - stream_last_updated_at

            if stream_time_diff > datetime.timedelta(seconds=self.STREAM_TIMEOUT_SECONDS):
                self._log.error(
                    "Stream not updated, restarting",
                    timeout_seconds=self.STREAM_TIMEOUT_SECONDS,
                    time_diff=str(stream_time_diff),
                )

                for task in self._stream_tasks:
                    if not task.done():
                        task.cancel()
