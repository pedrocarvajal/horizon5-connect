import argparse
import datetime
from multiprocessing import Queue
from typing import Any, Dict, Optional

from configs.timezone import TIMEZONE
from enums.command import Command
from interfaces.asset import AssetInterface
from providers.horizon_router import HorizonRouterProvider
from services.backtest.helpers.get_duration import get_duration
from services.logging import LoggingService
from services.ticks import TicksService


class BacktestService:
    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    _id: str
    _tick: TicksService
    _commands_queue: Queue
    _events_queue: Queue
    _horizon_router: Dict[str, Any]

    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(
        self,
        asset: AssetInterface,
        from_date: datetime.datetime,
        to_date: datetime.datetime,
        commands_queue: Optional[Queue] = None,
        events_queue: Optional[Queue] = None,
    ) -> None:
        parser = argparse.ArgumentParser()
        parser.add_argument("--restore-ticks", choices=["true", "false"])
        args = parser.parse_args()
        restore_ticks = args.restore_ticks == "true"

        self._id = None
        self._start_at = datetime.datetime.now(tz=TIMEZONE)
        self._from_date = from_date
        self._to_date = to_date
        self._restore_ticks = restore_ticks
        self._commands_queue = commands_queue
        self._events_queue = events_queue

        self._log = LoggingService()
        self._log.setup("backtest")
        self._log.info("Backtesting service started")

        self._asset = asset()
        self._tick = TicksService()
        self._horizon_router = HorizonRouterProvider()

        self._create_backtest()

        tick_setup = {
            "from_date": from_date,
            "to_date": to_date,
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

        self._asset.setup(
            backtest=True,
            backtest_id=self._id,
            **instances,
            **queues,
        )

    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def run(self) -> None:
        ticks = self._tick.ticks
        enabled_strategies = len(self._asset.strategies)

        if not self._id:
            self._log.error("Failed to create backtest...")
            self._kill()
            return

        if len(ticks) == 0:
            self._log.error("No ticks found")
            return

        if enabled_strategies == 0:
            self._log.error("No enabled strategies found")
            return

        for tick_model in ticks:
            self._asset.on_tick(tick_model)

        self._on_end()

    # ───────────────────────────────────────────────────────────
    # PRIVATE METHODS
    # ───────────────────────────────────────────────────────────
    def _on_end(self) -> None:
        start_timestamp = int(self._from_date.timestamp())
        end_timestamp = int(self._to_date.timestamp())
        expected_tick = int((end_timestamp - start_timestamp) / 60)

        end_at = datetime.datetime.now(TIMEZONE)
        quality = (len(self._tick.ticks) / expected_tick) * 100
        duration = get_duration(self._start_at, end_at)

        self._asset.on_end()
        self._kill()

        self._log.info(f"Backtest completed in: {duration} | Quality: {quality:.2f}% ")

    def _create_backtest(self) -> None:
        response = self._horizon_router.backtest_create(
            body={
                "asset": self._asset.symbol,
                "strategies": ",".join(
                    [strategy.id for strategy in self._asset.strategies]
                ),
                "from_date": int(self._from_date.timestamp()),
                "to_date": int(self._to_date.timestamp()),
            }
        )

        self._id = response["data"]["_id"]
        self._log.info(f"Backtest created: {response}")

    def _kill(self) -> None:
        self._commands_queue.put(
            {
                "command": Command.KILL,
            }
        )
