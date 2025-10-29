import datetime

from configs.timezone import TIMEZONE
from interfaces.asset import AssetInterface
from models.tick import TickModel
from services.backtest.handlers.session import SessionHandler
from services.backtest.handlers.tick import TickHandler
from services.backtest.helpers.get_duration_between_two_dates_human_readable import (
    get_duration_between_two_dates_human_readable,
)
from services.logging import LoggingService


class BacktestService:
    _tick: TickHandler
    _session: SessionHandler

    def __init__(
        self,
        asset: AssetInterface,
        from_date: datetime.datetime,
        to_date: datetime.datetime,
        restore_data: bool = False,
    ) -> None:
        self._start_at = datetime.datetime.now(tz=TIMEZONE)
        self._from_date = from_date
        self._to_date = to_date
        self._restore_data = restore_data

        tick_setup = {
            "from_date": from_date,
            "to_date": to_date,
            "restore_data": restore_data,
        }

        self._log = LoggingService()
        self._log.setup("backtest")

        self._asset = asset()
        self._session = SessionHandler(asset=self._asset)
        self._tick = TickHandler(asset=self._asset)

        self._session.setup()
        self._tick.setup(**tick_setup)
        self._asset.on_start()

    def run(self) -> None:
        start_timestamp = int(self._from_date.timestamp())
        end_timestamp = int(self._to_date.timestamp())
        expected_tick = int((end_timestamp - start_timestamp) / 60)
        ticks = self._tick.ticks

        self._log.info(f"Total ticks: {ticks.height}")
        self._log.info(f"Expected ticks: {expected_tick}")

        for tick in ticks.iter_rows(named=True):
            tick_model = TickModel()
            tick_model.date = datetime.datetime.fromtimestamp(tick["id"], tz=TIMEZONE)
            tick_model.price = tick["price"]
            self._asset.on_tick(tick_model)

        self._on_end()

    def _on_end(self) -> None:
        start_timestamp = int(self._from_date.timestamp())
        end_timestamp = int(self._to_date.timestamp())
        expected_tick = int((end_timestamp - start_timestamp) / 60)

        self._asset.on_end()

        end_at = datetime.datetime.now(TIMEZONE)
        quality = (self._tick.ticks.height / expected_tick) * 100
        duration = get_duration_between_two_dates_human_readable(self._start_at, end_at)

        self._log.info(
            f"Backtest completed in: {duration} | "
            f"Quality: {quality:.2f}% | "
            f"Session ID: {self._session.id}"
        )
