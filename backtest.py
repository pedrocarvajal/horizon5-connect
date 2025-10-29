import datetime
import tempfile
from pathlib import Path

import polars

from configs.assets import ASSETS
from configs.timezone import TIMEZONE
from helpers.get_progress_between_dates import get_progress_between_dates
from interfaces.asset import AssetInterface
from models.candlestick import CandlestickModel
from models.tick import TickModel
from services.logging import LoggingService


class Backtest:
    _ticks_folder: Path = Path(tempfile.gettempdir()) / "horizon-connect" / "ticks"

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

        self._log = LoggingService()
        self._log.setup("backtest")

        self._asset = asset()
        self._asset.on_start()

        self._download_data()

    def run(self) -> None:
        ticks_folder = self._ticks_folder / self._asset.symbol
        start_timestamp = int(self._from_date.timestamp())
        end_timestamp = int(self._to_date.timestamp())
        expected_ticks = int((end_timestamp - start_timestamp) / 60)

        ticks_file = polars.scan_parquet(ticks_folder / "ticks.parquet")
        ticks = (
            ticks_file.filter(
                (polars.col("id") >= start_timestamp)
                & (polars.col("id") <= end_timestamp)
            )
            .sort("id")
            .collect(engine="streaming")
        )

        self._log.info(f"Total ticks: {ticks.height}")
        self._log.info(f"Expected ticks: {expected_ticks}")

        for tick in ticks.iter_rows(named=True):
            tick_model = TickModel()
            tick_model.date = datetime.datetime.fromtimestamp(tick["id"], tz=TIMEZONE)
            tick_model.price = tick["price"]
            self._asset.on_tick(tick_model)

        quality = (ticks.height / expected_ticks) * 100
        missing_ticks = expected_ticks - ticks.height

        self._log.info(f"Data quality: {quality:.2f}%")
        self._log.info(f"Missing ticks: {missing_ticks}")

        self._asset.on_end()

        self._end_at = datetime.datetime.now(TIMEZONE)
        self._log.info(f"Backtest completed in {self._get_duration()}")

    def _download_data(self) -> None:
        if not self._restore_data:
            return

        self._log.info(f"Downloading data for {self._asset.symbol}")
        self._log.info(f"From date: {self._from_date}")
        self._log.info(f"To date: {self._to_date}")

        current_date = None
        start_timestamp = int(self._from_date.timestamp())
        end_timestamp = int(self._to_date.timestamp())
        candlesticks = []

        def _process_klines(klines: list[CandlestickModel]) -> None:
            nonlocal current_date
            nonlocal candlesticks
            candlesticks.extend([kline.to_dict() for kline in klines])
            current_date = candlesticks[-1]["kline_close_time"]

            progress = (
                get_progress_between_dates(
                    start_date_in_timestamp=start_timestamp,
                    end_date_in_timestamp=end_timestamp,
                    current_date_in_timestamp=int(current_date.timestamp()),
                )
                * 100
            )

            current_date_formatted = current_date.strftime("%Y-%m-%d %H:%M:%S")
            end_date_formatted = self._to_date.strftime("%Y-%m-%d %H:%M:%S")
            start_date_formatted = self._from_date.strftime("%Y-%m-%d %H:%M:%S")

            self._log.info(
                f"Downloading symbol: {self._asset.symbol}"
                f" | Starting time: {start_date_formatted}"
                f" | Current time: {current_date_formatted}"
                f" | Ending time: {end_date_formatted}"
                f" | Progress: {progress:.2f}%"
            )

        self._asset.gateway.get_klines(
            symbol=self._asset.symbol,
            timeframe="1m",
            from_date=self._from_date,
            to_date=self._to_date,
            callback=_process_klines,
        )

        # Saving data
        ticks_folder = self._ticks_folder / self._asset.symbol
        ticks_folder.mkdir(parents=True, exist_ok=True)
        candlesticks = polars.DataFrame(candlesticks)
        ticks = candlesticks.select(
            [
                polars.col("kline_open_time")
                .dt.epoch("s")
                .cast(polars.Int64)
                .alias("id"),
                polars.col("close_price").alias("price"),
            ]
        )

        ticks.write_parquet(ticks_folder / "ticks.parquet")
        self._log.info(f"Data saved to {ticks_folder / 'ticks.parquet'}")
        self._log.info(f"Total ticks: {ticks.height}")

    def _get_duration(self) -> str:
        total_seconds = (self._end_at - self._start_at).total_seconds()
        seconds_in_minute = 60
        seconds_in_hour = 3600
        seconds_in_day = 86400

        if total_seconds < seconds_in_minute:
            seconds = int(total_seconds)
            return f"{seconds} seconds"

        if total_seconds < seconds_in_hour:
            minutes = int(total_seconds / seconds_in_minute)
            return f"{minutes} minutes"

        if total_seconds < seconds_in_day:
            hours = int(total_seconds / seconds_in_hour)
            return f"{hours} hours"

        days = int(total_seconds / seconds_in_day)
        return f"{days} days"


if __name__ == "__main__":
    to_date = datetime.datetime.now(tz=TIMEZONE)
    from_date = to_date - datetime.timedelta(days=365)

    backtest = Backtest(
        asset=ASSETS["btcusdt"],
        from_date=from_date,
        to_date=to_date,
        # restore_data=True,
    )

    backtest.run()
