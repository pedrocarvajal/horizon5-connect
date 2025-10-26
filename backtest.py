import datetime
import shutil
import tempfile
from pathlib import Path

import polars

from configs.assets import ASSETS
from configs.timezone import TIMEZONE
from interfaces.asset import AssetInterface
from models.candlestick import CandlestickModel
from models.tick import TickModel
from services.logging import LoggingService


class Backtest:
    _ticks_folder: Path = Path(tempfile.gettempdir()) / "horizon-connect" / "ticks"
    _data_total_ticks: int = 0
    _data_total_missing_prices: int = 0

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

        self._prepare_data()
        self._download_data()

    def run(self) -> None:
        ticks_folder = self._ticks_folder / self._asset.symbol
        start_timestamp = int(self._from_date.timestamp())
        end_timestamp = int(self._to_date.timestamp())
        files = polars.scan_parquet(ticks_folder / "*.parquet")
        ticks = (
            files.filter(
                (polars.col("id") >= start_timestamp)
                & (polars.col("id") <= end_timestamp)
            )
            .sort("id")
            .collect(engine="streaming")
        )

        for tick in ticks.iter_rows(named=True):
            tick_model = TickModel()
            tick_model.date = datetime.datetime.fromtimestamp(tick["id"], tz=TIMEZONE)
            tick_model.price = tick["price"]

            self._data_total_ticks += 1

            if tick_model.price == 0:
                self._data_total_missing_prices += 1
                continue

            self._asset.on_tick(tick_model)

        quality = (
            (self._data_total_ticks - self._data_total_missing_prices)
            / self._data_total_ticks
        ) * 100

        self._log.info(f"Data quality: {quality:.2f}%")
        self._log.info(f"Total ticks: {self._data_total_ticks}")
        self._log.info(f"Total missing prices: {self._data_total_missing_prices}")

        self._asset.on_end()

        self._end_at = datetime.datetime.now(TIMEZONE)
        self._log.info(f"Backtest completed in {self._get_duration()}")

    def _prepare_data(self) -> None:
        self._log.info(f"Using {self._ticks_folder}.")

        if not self._restore_data:
            return

        ticks_folder = self._ticks_folder / self._asset.symbol

        if ticks_folder.exists():
            shutil.rmtree(ticks_folder, ignore_errors=True)
            self._log.info(f"Ticks folder removed: {ticks_folder}")

        ticks_folder.mkdir(parents=True, exist_ok=True)

        self._log.info(f"Preparing data for {self._asset.symbol}")
        self._log.info(f"From date: {self._from_date}")
        self._log.info(f"To date: {self._to_date}")
        self._log.info(f"Ticks folder: {ticks_folder}")

        current_month_start = self._from_date.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        end_month = self._to_date.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        total_records = 0

        while current_month_start <= end_month:
            year = current_month_start.year
            month = current_month_start.month

            if month == 12:
                next_month = current_month_start.replace(year=year + 1, month=1)
            else:
                next_month = current_month_start.replace(month=month + 1)

            month_start = max(current_month_start, self._from_date)
            month_end = min(next_month - datetime.timedelta(seconds=1), self._to_date)

            timestamps = []
            prices = []
            updated_ats = []
            current_minute = month_start

            while current_minute <= month_end:
                timestamps.append(int(current_minute.timestamp()))
                prices.append(0.0)
                updated_ats.append(datetime.datetime.now(tz=TIMEZONE))
                current_minute += datetime.timedelta(minutes=1)
                total_records += 1

            data = polars.DataFrame(
                {
                    "id": timestamps,
                    "price": prices,
                    "updated_at": updated_ats,
                }
            )

            data_path = ticks_folder / f"{year}-{month:02d}.parquet"
            data.write_parquet(data_path)

            traveled = current_month_start.timestamp() - self._from_date.timestamp()
            total = self._to_date.timestamp() - self._from_date.timestamp()
            progress = (traveled / total * 100) if total != 0 else 100.0

            month_formatted = current_month_start.strftime("%Y-%m")
            start_date_formatted = self._from_date.strftime("%Y-%m-%d %H:%M:%S")
            end_date_formatted = self._to_date.strftime("%Y-%m-%d %H:%M:%S")

            self._log.info(
                f"Preparing symbol: {self._asset.symbol}"
                f" | Starting time: {start_date_formatted}"
                f" | Current month: {month_formatted}"
                f" | Ending time: {end_date_formatted}"
                f" | Progress: {progress:.2f}%"
            )

            current_month_start = next_month

        self._log.info(f"{total_records} records prepared to be filled.")

    def _download_data(self) -> None:
        if not self._restore_data:
            return

        self._log.info(f"Downloading data for {self._asset.symbol}")
        self._log.info(f"From date: {self._from_date}")
        self._log.info(f"To date: {self._to_date}")

        current_date = None
        start_timestamp = int(self._from_date.timestamp())
        end_timestamp = int(self._to_date.timestamp())
        monthly_updates: dict[str, dict[int, float]] = {}

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
                year = kline.kline_open_time.year
                month = kline.kline_open_time.month
                month_key = f"{year}-{month:02d}"

                if month_key not in monthly_updates:
                    monthly_updates[month_key] = {}

                monthly_updates[month_key][timestamp] = kline.open_price
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

        total_months = len(monthly_updates)
        self._log.info(f"Updating {total_months} monthly files with data")

        for month_key, updates in monthly_updates.items():
            ticks_folder = self._ticks_folder / self._asset.symbol
            data_path = ticks_folder / f"{month_key}.parquet"
            df = polars.read_parquet(data_path)

            updates_df = polars.DataFrame(
                {
                    "id": list(updates.keys()),
                    "new_price": list(updates.values()),
                }
            )

            df = df.join(updates_df, on="id", how="left")
            df = df.with_columns(
                polars.when(polars.col("new_price").is_not_null())
                .then(polars.col("new_price"))
                .otherwise(polars.col("price"))
                .alias("price")
            )

            df = df.drop("new_price")
            df = df.with_columns(
                polars.lit(datetime.datetime.now(tz=TIMEZONE)).alias("updated_at")
            )

            df.write_parquet(data_path)

            self._log.info(f"Updated {month_key}.parquet with {len(updates)} prices")

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
    backtest = Backtest(
        asset=ASSETS["btcusdt"],
        from_date=datetime.datetime(2019, 10, 1, tzinfo=TIMEZONE),
        to_date=datetime.datetime(2025, 10, 1, tzinfo=TIMEZONE),
        restore_data=True,
    )

    backtest.run()
