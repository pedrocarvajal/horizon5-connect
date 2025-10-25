import datetime

from configs.assets import ASSETS
from configs.timezone import TIMEZONE
from interfaces.asset import AssetInterface
from models.tick import TickModel
from services.logging import LoggingService


class Backtest:
    def __init__(
        self,
        asset: AssetInterface,
        from_date: datetime.datetime,
        to_date: datetime.datetime,
    ) -> None:
        self._start_at = datetime.datetime.now(tz=TIMEZONE)
        self._from_date = from_date
        self._to_date = to_date

        self._asset = asset()
        self._asset.on_start()

        self._logging = LoggingService()
        self._logging.setup(__name__)

        self._logging.info(f"Initializing backtest for {self._asset._symbol}")

    def _get_duration(self) -> str:
        start_at = getattr(self, "_start_at", None)
        end_at = getattr(self, "_end_at", None)
        total_seconds = (end_at - start_at).total_seconds()
        seconds_in_minute = 60
        seconds_in_hour = 3600
        seconds_in_day = 86400

        if total_seconds < seconds_in_minute:
            response = f"{int(total_seconds)} seconds"
        elif total_seconds < seconds_in_hour:
            response = f"{int(total_seconds / seconds_in_minute)} minutes"
        elif total_seconds < seconds_in_day:
            response = f"{int(total_seconds / seconds_in_hour)} hours"
        else:
            response = f"{int(total_seconds / seconds_in_day)} days"

        return response

    def _get_tick(self, date: datetime.datetime) -> TickModel:
        tick = TickModel()
        tick.date = date
        tick.price = 0

        return tick

    def run(self) -> None:
        current_date = self._from_date

        self._logging.info(
            f"Running backtest from {self._from_date} to {self._to_date}"
        )

        while current_date <= self._to_date:
            current_date += datetime.timedelta(minutes=1)
            self._asset.on_tick(self._get_tick(current_date))

        self._asset.on_end()

        self._end_at = datetime.datetime.now(TIMEZONE)
        self._logging.info(f"Backtest completed in {self._get_duration()}")


if __name__ == "__main__":
    backtest = Backtest(
        asset=ASSETS["btcusdt"],
        from_date=datetime.datetime(2019, 10, 1, tzinfo=TIMEZONE),
        to_date=datetime.datetime(2025, 10, 24, tzinfo=TIMEZONE),
    )

    backtest.run()
