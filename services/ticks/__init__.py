import datetime
import tempfile
from pathlib import Path
from typing import Any, Dict, List

import polars

from configs.timezone import TIMEZONE
from helpers.get_progress_between_dates import get_progress_between_dates
from interfaces.asset import AssetInterface
from models.tick import TickModel
from services.logging import LoggingService


class TicksService:
    # ───────────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────────
    _ticks_folder: Path = Path(tempfile.gettempdir()) / "horizon-connect" / "ticks"
    _asset: AssetInterface
    _from_date: datetime.datetime
    _to_date: datetime.datetime
    _restore_ticks: bool
    _log: LoggingService

    # ───────────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────────
    def __init__(self) -> None:
        self._log = LoggingService()
        self._log.setup("ticks_service")

    # ───────────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────────
    def setup(self, **kwargs: Any) -> None:
        self._asset = kwargs.get("asset")
        self._to_date = datetime.datetime.now(tz=TIMEZONE)
        self._from_date = self._to_date - datetime.timedelta(days=365 * 25)
        self._restore_ticks = kwargs.get("restore_ticks")

        if self._asset is None:
            raise ValueError("Asset is required")

        if self._from_date is None:
            raise ValueError("From date is required")

        if self._to_date is None:
            raise ValueError("To date is required")

        if self._restore_ticks is None:
            raise ValueError("Restore data is required")

        self._download()

    # ───────────────────────────────────────────────────────────────
    # PRIVATE METHODS
    # ───────────────────────────────────────────────────────────────
    def _get_datetime_from_timestamp(self, timestamp: int) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(timestamp, tz=TIMEZONE)

    def _get_formatted_timestamp(self, timestamp: int) -> str:
        return self._get_datetime_from_timestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")

    def _get_download_start_date(self, parquet_file: Path) -> datetime.datetime:
        if self._restore_ticks:
            if parquet_file.exists():
                self._log.info(f"Deleting existing data for {self._asset.symbol}")
                parquet_file.unlink()

            return self._from_date

        if parquet_file.exists():
            existing_ticks = polars.scan_parquet(parquet_file)
            last_tick = existing_ticks.select(polars.col("id").max()).collect()
            last_timestamp = last_tick[0, "id"]
            date = self._get_datetime_from_timestamp(last_timestamp)

            self._log.info(f"Resuming download from {date}")
            return date

        self._log.info("No existing data found, starting fresh download")
        return self._from_date

    def _save_ticks(
        self,
        candlesticks: List[Dict[str, Any]],
        parquet_file: Path,
        ticks_folder: Path,
    ) -> None:
        ticks_folder.mkdir(parents=True, exist_ok=True)
        candlesticks_data = polars.DataFrame(candlesticks)
        new_ticks = candlesticks_data.select(
            [
                (polars.col("close_time")).cast(polars.Int64).alias("id"),
                polars.col("close_price").alias("price"),
            ]
        )

        if self._restore_ticks or not parquet_file.exists():
            new_ticks.write_parquet(parquet_file)
        else:
            existing_ticks = polars.read_parquet(parquet_file)
            combined_ticks = polars.concat([existing_ticks, new_ticks])
            combined_ticks = combined_ticks.unique(subset=["id"]).sort("id")
            combined_ticks.write_parquet(parquet_file)

        final_ticks = polars.read_parquet(parquet_file)
        actual_start_date = self._get_datetime_from_timestamp(final_ticks[0, "id"])
        actual_end_date = self._get_datetime_from_timestamp(final_ticks[-1, "id"])

        self._log.info(f"Data saved to {parquet_file}")
        self._log.info(f"Total ticks: {final_ticks.height}")
        self._log.info(f"Actual date range: {actual_start_date} to {actual_end_date}")

    def _download(self) -> None:
        ticks_folder = self._ticks_folder / self._asset.symbol
        parquet_file = ticks_folder / "ticks.parquet"
        download_from_date = self._get_download_start_date(parquet_file)

        self._log.info(f"Downloading data for {self._asset.symbol}")
        self._log.info(f"From date: {download_from_date}")
        self._log.info(f"To date: {self._to_date}")

        current_date = None
        start_timestamp = int(download_from_date.timestamp())
        end_timestamp = int(self._to_date.timestamp())
        candlesticks = []

        def _process_klines(klines: List[Dict[str, Any]]) -> None:
            nonlocal current_date
            nonlocal candlesticks

            if not klines:
                if not candlesticks:
                    message = (
                        f"No data available for {self._asset.symbol} from "
                        f"{download_from_date}. Symbol might not have "
                        f"historical data for the requested period."
                    )
                    self._log.warning(message)
                return

            candlesticks.extend(klines)
            current_date = candlesticks[-1]["close_time"]
            progress = (
                get_progress_between_dates(
                    start_date_in_timestamp=start_timestamp,
                    end_date_in_timestamp=end_timestamp,
                    current_date_in_timestamp=current_date,
                )
                * 100
            )

            current_date_formatted = self._get_formatted_timestamp(current_date)
            end_date_formatted = self._get_formatted_timestamp(end_timestamp)
            start_date_formatted = self._get_formatted_timestamp(start_timestamp)

            self._log.info(
                f"Downloading symbol: {self._asset.symbol}"
                f" | Starting time: {start_date_formatted}"
                f" | Current time: {current_date_formatted}"
                f" | Ending time: {end_date_formatted}"
                f" | Progress: {progress:.2f}%"
            )

        try:
            gateway = self._asset.gateway
            gateway.get_klines(
                symbol=self._asset.symbol,
                timeframe="1m",
                from_date=int(download_from_date.timestamp()),
                to_date=int(self._to_date.timestamp()),
                callback=_process_klines,
            )

        except Exception as e:
            self._log.error(f"Error downloading data for {self._asset.symbol}: {e}")
            if not candlesticks:
                raise

        if not candlesticks:
            self._log.warning(f"No data downloaded for {self._asset.symbol}")
            return

        self._save_ticks(candlesticks, parquet_file, ticks_folder)

    # ───────────────────────────────────────────────────────────────
    # GETTERS
    # ───────────────────────────────────────────────────────────────
    @property
    def folder(self) -> Path:
        return self._ticks_folder

    @property
    def ticks(self) -> List[TickModel]:
        response = []
        ticks_folder = self.folder / self._asset.symbol
        ticks = polars.scan_parquet(ticks_folder / "ticks.parquet")

        filtered_ticks = (
            ticks.filter(
                (polars.col("id") >= int(self._from_date.timestamp()))
                & (polars.col("id") <= int(self._to_date.timestamp()))
            )
            .sort("id")
            .collect(engine="streaming")
        )

        for tick_row in filtered_ticks.iter_rows(named=True):
            price = tick_row["price"]
            date = self._get_datetime_from_timestamp(tick_row["id"])

            tick = TickModel()
            tick.date = date
            tick.price = price
            response.append(tick)

        return response
