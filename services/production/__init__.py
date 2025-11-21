import asyncio
import datetime
from multiprocessing import Queue
from typing import Any, List, Optional

from configs.timezone import TIMEZONE
from helpers.get_portfolio_by_path import get_portfolio_by_path
from interfaces.asset import AssetInterface
from interfaces.portfolio import PortfolioInterface
from models.tick import TickModel
from services.logging import LoggingService
from services.ticks import TicksService


class ProductionService:
    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    _portfolio: PortfolioInterface
    _portfolio_path: Optional[str]
    _assets: List[AssetInterface]

    _stream_started_at: datetime.datetime
    _stream_last_updated_at: datetime.datetime
    _stream_tasks: List[asyncio.Task[None]]

    _commands_queue: Optional[Queue]
    _events_queue: Optional[Queue]

    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(self, **kwargs: Any) -> None:
        self._log = LoggingService()
        self._log.setup("production_service")

        self._assets = []
        self._stream_started_at = datetime.datetime.now(tz=TIMEZONE)
        self._stream_last_updated_at = datetime.datetime.now(tz=TIMEZONE)
        self._stream_tasks = []

        self._commands_queue = kwargs.get("commands_queue")
        self._events_queue = kwargs.get("events_queue")
        self._portfolio_path = kwargs.get("portfolio_path")

    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def setup(self) -> None:
        if not self._commands_queue:
            raise ValueError("Commands queue is required")

        if not self._events_queue:
            raise ValueError("Events queue is required")

        if not self._portfolio_path:
            raise ValueError("Portfolio is required")

        self._portfolio = get_portfolio_by_path(
            self._portfolio_path,
        )

        if not self._portfolio:
            raise ValueError("Portfolio not found")

    def run(self) -> None:
        for asset in self._portfolio.assets:
            self._assets.append(asset())

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

    # ───────────────────────────────────────────────────────────
    # PRIVATE METHODS
    # ───────────────────────────────────────────────────────────
    async def _run_tasks(self) -> None:
        await asyncio.gather(
            self._connect(),
            self._supervisor(),
        )

    async def _supervisor(self) -> None:
        while True:
            await asyncio.sleep(10)

            stream_last_updated_at = self._stream_last_updated_at
            stream_time_diff = datetime.datetime.now(tz=TIMEZONE) - stream_last_updated_at

            if stream_time_diff > datetime.timedelta(seconds=10):
                self._log.error(
                    f"Stream has not been updated in the last 10 seconds: {stream_time_diff}. Restarting stream..."
                )

                for task in self._stream_tasks:
                    if not task.done():
                        task.cancel()

    def _collect_historical(self) -> None:
        for asset in self._assets:
            tick_service = TicksService()
            tick_service.setup(
                asset=asset,
                restore_ticks=False,
                disable_download=False,
            )

            to_date = datetime.datetime.now(tz=TIMEZONE)
            from_date = to_date - datetime.timedelta(days=365)

            self._log.info(f"Collecting historical data for {asset.symbol} from {from_date} to {to_date}")

            ticks = tick_service.ticks(
                from_date=from_date,
                to_date=to_date,
            )

            self._log.info(f"Injecting {len(ticks)} ticks for {asset.symbol}")

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
                f"Error connecting to gateway stream: {e} | Asset: {asset.symbol} | Gateway: {gateway.name}"
            )
