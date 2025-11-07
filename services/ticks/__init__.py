import datetime
import tempfile
from pathlib import Path
from typing import Any, Dict, List

import polars

from configs.timezone import TIMEZONE
from helpers.get_progress_between_dates import get_progress_between_dates
from models.tick import TickModel
from services.logging import LoggingService


class TicksService:
    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    _ticks_folder: Path = Path(tempfile.gettempdir()) / "horizon-connect" / "ticks"
    _asset: str
    _from_date: datetime.datetime
    _to_date: datetime.datetime
    _restore_ticks: bool
    _log: LoggingService

    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(self) -> None:
        self._log = LoggingService()
        self._log.setup("ticks_service")

    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def setup(self, **kwargs: Any) -> None:
        self._asset = kwargs.get("asset")
        self._from_date = kwargs.get("from_date")
        self._to_date = kwargs.get("to_date")
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

    # ───────────────────────────────────────────────────────────
    # PRIVATE METHODS
    # ───────────────────────────────────────────────────────────
    def _download(self) -> None:
        if not self._restore_ticks:
            return

        self._log.info(f"Downloading data for {self._asset}")
        self._log.info(f"From date: {self._from_date}")
        self._log.info(f"To date: {self._to_date}")

        current_date = None
        start_timestamp = int(self._from_date.timestamp())
        end_timestamp = int(self._to_date.timestamp())
        candlesticks = []

        def _process_klines(klines: List[Dict[str, Any]]) -> None:
            nonlocal current_date
            nonlocal candlesticks
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

            current_date_formatted = datetime.datetime.fromtimestamp(
                current_date,
                tz=TIMEZONE,
            ).strftime("%Y-%m-%d %H:%M:%S")

            end_date_formatted = datetime.datetime.fromtimestamp(
                end_timestamp,
                tz=TIMEZONE,
            ).strftime("%Y-%m-%d %H:%M:%S")

            start_date_formatted = datetime.datetime.fromtimestamp(
                start_timestamp,
                tz=TIMEZONE,
            ).strftime("%Y-%m-%d %H:%M:%S")

            self._log.info(
                f"Downloading symbol: {self._asset}"
                f" | Starting time: {start_date_formatted}"
                f" | Current time: {current_date_formatted}"
                f" | Ending time: {end_date_formatted}"
                f" | Progress: {progress:.2f}%"
            )

        self._asset.gateway.get_klines(
            symbol=self._asset,
            timeframe="1m",
            from_date=self._from_date,
            to_date=self._to_date,
            callback=_process_klines,
        )

        ticks_folder = self._ticks_folder / self._asset
        ticks_folder.mkdir(parents=True, exist_ok=True)
        candlesticks = polars.DataFrame(candlesticks)
        ticks = candlesticks.select(
            [
                (polars.col("close_time")).cast(polars.Int64).alias("id"),
                polars.col("close_price").alias("price"),
            ]
        )

        ticks.write_parquet(ticks_folder / "ticks.parquet")
        self._log.info(f"Data saved to {ticks_folder / 'ticks.parquet'}")
        self._log.info(f"Total ticks: {ticks.height}")

    # ───────────────────────────────────────────────────────────
    # GETTERS
    # ───────────────────────────────────────────────────────────
    @property
    def folder(self) -> Path:
        return self._ticks_folder

    @property
    def ticks(self) -> List[TickModel]:
        response = []
        ticks_folder = self.folder / self._asset
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
            date = datetime.datetime.fromtimestamp(
                tick_row["id"],
                tz=TIMEZONE,
            )

            tick = TickModel()
            tick.date = date
            tick.price = price
            response.append(tick)

        return response
