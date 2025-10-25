import datetime
from pathlib import Path

import polars

from configs.assets import ASSETS
from configs.timezone import TIMEZONE
from interfaces.asset import AssetInterface
from models.candlestick import CandlestickModel
from models.tick import TickModel
from services.logging import LoggingService


class Backtest:
    _ticks_folder: Path = Path("storage/ticks")

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

        self._asset = asset()
        self._asset.on_start()

        self._log = LoggingService()
        self._log.setup("backtest")

        self._prepare_data()
        self._download_data()

        self._log.info(f"Initializing backtest for {self._asset._symbol}")

    def run(self) -> None:
        current_date = self._from_date

        self._log.info(f"Running backtest from {self._from_date} to {self._to_date}")

        while current_date <= self._to_date:
            current_date += datetime.timedelta(minutes=1)
            self._asset.on_tick(self._get_tick(current_date))

        self._asset.on_end()

        self._end_at = datetime.datetime.now(TIMEZONE)
        self._log.info(f"Backtest completed in {self._get_duration()}")

    def _prepare_data(self) -> None:
        if not self._restore_data:
            self._log.info("Data will not be restored, using existing data.")
            return

        records = 0
        current_date = self._from_date - datetime.timedelta(days=1)
        ticks_folder = self._ticks_folder / self._asset.symbol
        ticks_folder.parent.mkdir(parents=True, exist_ok=True)

        self._log.info(f"Preparing data for {self._asset.symbol}")
        self._log.info(f"From date: {self._from_date}")
        self._log.info(f"To date: {self._to_date}")
        self._log.info(f"Ticks folder: {ticks_folder}")

        for item in ticks_folder.glob("*"):
            if item.is_file():
                item.unlink()

        while current_date <= self._to_date:
            records += 1
            current_date += datetime.timedelta(minutes=1)
            timestamp = int(current_date.timestamp())
            data_path = ticks_folder / f"{timestamp}.parquet"
            data_path.parent.mkdir(parents=True, exist_ok=True)
            data = polars.DataFrame(
                {
                    "id": timestamp,
                    "price": 0.0,
                    "_": None,
                    "updated_at": datetime.datetime.now(tz=TIMEZONE),
                }
            )

            data.write_parquet(data_path)

        self._log.info(f"{records} records prepared to be filled.")

    def _download_data(self) -> None:
        self._log.info(f"Downloading data for {self._asset.symbol}")
        self._log.info(f"From date: {self._from_date}")
        self._log.info(f"To date: {self._to_date}")

        current_date = None
        start_timestamp = int(self._from_date.timestamp())
        end_timestamp = int(self._to_date.timestamp())

        def _get_progress(current_time: int) -> float:
            traveled_time = current_time - start_timestamp
            total_time = end_timestamp - start_timestamp

            if total_time == 0:
                return 100.0

            return float((traveled_time / total_time) * 100)

        def _process_klines(klines: list[CandlestickModel]) -> None:
            nonlocal current_date

            for kline in klines:
                timestamp = int(kline.kline_open_time.timestamp())
                data_file_name = f"{timestamp}.parquet"
                data_path = self._ticks_folder / self._asset.symbol / data_file_name
                data_path_exists = data_path.exists()

                if not data_path_exists:
                    continue

                data = polars.DataFrame(
                    {
                        "id": timestamp,
                        "price": kline.open_price,
                        "_": kline.to_dict(),
                        "updated_at": datetime.datetime.now(tz=TIMEZONE),
                    }
                )

                data.write_parquet(data_path)
                current_date = kline.kline_open_time

            if current_date:
                progress = _get_progress(int(current_date.timestamp()))
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

    def _get_duration(self) -> str:
        start_at = getattr(self, "_start_at", None)
        end_at = getattr(self, "_end_at", None)
        total_seconds = (end_at - start_at).total_seconds()
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

    def _get_tick(self, date: datetime.datetime) -> TickModel:
        tick = TickModel()
        tick.date = date
        tick.price = 0

        return tick


if __name__ == "__main__":
    backtest = Backtest(
        asset=ASSETS["btcusdt"],
        from_date=datetime.datetime(2025, 9, 1, tzinfo=TIMEZONE),
        to_date=datetime.datetime(2025, 10, 1, tzinfo=TIMEZONE),
        restore_data=True,
    )

    backtest.run()
