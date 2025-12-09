"""Ticks service for downloading and managing historical tick data."""

import datetime
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple

import polars

from configs.timezone import TIMEZONE
from helpers.get_progress_between_dates import get_progress_between_dates
from interfaces.asset import AssetInterface
from interfaces.ticks import TicksInterface
from models.tick import TickModel
from services.gateway.models.gateway_kline import GatewayKlineModel
from services.logging import LoggingService


@dataclass
class DownloadTask:
    """Task for parallel download of tick data."""

    asset: AssetInterface
    restore_ticks: bool = False


class TicksService(TicksInterface):
    """Service for downloading and managing historical tick data."""

    _PROJECT_ROOT: Path = Path(__file__).parent.parent.parent
    _SECONDS_PER_MINUTE: int = 60
    _TIMELINE_START_DATE: datetime.datetime = datetime.datetime(2000, 6, 1, 0, 0, 0, tzinfo=TIMEZONE)

    _asset: Optional[AssetInterface] = None
    _is_download_disabled: bool = False
    _should_restore_ticks: bool = False
    _ticks_folder: Path = _PROJECT_ROOT / "storage" / "ticks"

    _log: LoggingService

    def __init__(self) -> None:
        """Initialize ticks service."""
        self._log = LoggingService()

    def get_timeline(
        self,
        from_date: datetime.datetime,
        to_date: datetime.datetime,
    ) -> List[int]:
        """Generate timeline of timestamps from from_date to to_date."""
        return self._generate_timeline(from_date, to_date)

    def iterate_ticks(
        self,
        symbols: List[str],
        from_date: datetime.datetime,
        to_date: datetime.datetime,
    ) -> Iterator[Tuple[datetime.datetime, Dict[str, TickModel]]]:
        """Iterate over timeline yielding ticks for each timestamp using direct index access."""
        assets_arrays = self._load_assets_arrays(symbols, from_date, to_date)
        timeline = self.get_timeline(from_date, to_date)

        if assets_arrays:
            min_array_length = min(len(array) for array in assets_arrays.values())
            timeline = timeline[:min_array_length]

        for index, timestamp in enumerate(timeline):
            tick_date = self._get_datetime_from_timestamp(timestamp)
            ticks: Dict[str, TickModel] = {}

            for symbol in symbols:
                close_array = assets_arrays.get(symbol)

                if close_array is None:
                    continue

                close_price = close_array[index]

                if close_price is None:
                    continue

                ticks[symbol] = TickModel(
                    date=tick_date,
                    price=close_price,
                    is_simulated=True,
                )

            yield (tick_date, ticks)

    def load_assets_data(
        self,
        symbols: List[str],
        from_date: datetime.datetime,
        to_date: datetime.datetime,
    ) -> Dict[str, polars.DataFrame]:
        """Load parquet data for multiple assets into memory."""
        assets_data: Dict[str, polars.DataFrame] = {}
        from_timestamp = int(from_date.timestamp())
        to_timestamp = int(to_date.timestamp())

        for symbol in symbols:
            parquet_path = self._get_parquet_path(symbol)

            if not parquet_path.exists():
                self._log.warning(f"No parquet file for {symbol}")
                continue

            dataframe = (
                polars.scan_parquet(parquet_path)  # pyright: ignore[reportUnknownMemberType]
                .filter((polars.col("timestamp") >= from_timestamp) & (polars.col("timestamp") <= to_timestamp))
                .collect()
            )

            assets_data[symbol] = dataframe.set_sorted("timestamp")
            self._log.info(f"Loaded {dataframe.height:,} rows for {symbol}")

        return assets_data

    def setup(self, **kwargs: Any) -> None:
        """Configure ticks service with asset and download options."""
        self._asset = kwargs.get("asset")
        self._should_restore_ticks = kwargs.get("restore_ticks", False)
        self._is_download_disabled = kwargs.get("disable_download", False)

        if self._asset is None:
            raise ValueError("Asset is required")

        assert self._asset is not None
        self._download()

    def ticks(
        self,
        from_date: datetime.datetime,
        to_date: datetime.datetime,
    ) -> List[TickModel]:
        """Retrieve tick data for the specified date range."""
        assert self._asset is not None
        response: List[TickModel] = []
        parquet_file = self._get_parquet_path(self._asset.symbol)
        ticks = polars.scan_parquet(parquet_file)  # pyright: ignore[reportUnknownMemberType]
        from_timestamp = int(from_date.timestamp())
        to_timestamp = int(to_date.timestamp())

        filtered_ticks = (
            ticks.filter(
                (polars.col("timestamp") >= from_timestamp)
                & (polars.col("timestamp") <= to_timestamp)
                & (polars.col("close").is_not_null())
            )
            .sort("timestamp")
            .collect(engine="streaming")
        )

        for tick_row in filtered_ticks.iter_rows(named=True):
            date = self._get_datetime_from_timestamp(tick_row["timestamp"])
            price = tick_row["close"]

            tick = TickModel(
                date=date,
                price=price,
                is_simulated=True,
            )
            response.append(tick)

        return response

    def _atomic_write_parquet(self, dataframe: polars.DataFrame, target_path: Path) -> None:
        """Write parquet file atomically to prevent corruption on interruption."""
        target_path.parent.mkdir(parents=True, exist_ok=True)
        temp_file = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb",
                suffix=".parquet.tmp",
                dir=target_path.parent,
                delete=False,
            ) as temp_file_handle:
                temp_file = Path(temp_file_handle.name)
            dataframe.write_parquet(temp_file)
            temp_file.rename(target_path)
        except Exception:
            if temp_file and temp_file.exists():
                temp_file.unlink()
            raise

    def _download(self) -> None:
        assert self._asset is not None
        if self._is_download_disabled:
            return

        parquet_file = self._get_parquet_path(self._asset.symbol)
        download_from_date = self._get_download_start_date(parquet_file)
        download_to_date = datetime.datetime.now(tz=TIMEZONE)

        self._log.info(f"Downloading data for {self._asset.symbol}")
        self._log.info(f"From date: {download_from_date}")
        self._log.info(f"To date: {download_to_date}")

        current_date = None
        actual_start_timestamp: Optional[int] = None
        end_timestamp = int(download_to_date.timestamp())
        klines: List[GatewayKlineModel] = []
        asset = self._asset
        assert asset is not None

        def _process_klines(new_klines: List[GatewayKlineModel]) -> None:
            nonlocal current_date
            nonlocal klines
            nonlocal actual_start_timestamp

            if not new_klines:
                return

            klines.extend(new_klines)

            if actual_start_timestamp is None:
                actual_start_timestamp = klines[0].close_time

            current_date = klines[-1].close_time
            progress = min(
                get_progress_between_dates(
                    start_date_in_timestamp=actual_start_timestamp,
                    end_date_in_timestamp=end_timestamp,
                    current_date_in_timestamp=current_date,
                )
                * 100,
                100.0,
            )

            current_date_formatted = self._get_formatted_timestamp(current_date)
            end_date_formatted = self._get_formatted_timestamp(end_timestamp)
            start_date_formatted = self._get_formatted_timestamp(actual_start_timestamp)
            times = f"Start: {start_date_formatted} | Current: {current_date_formatted} | End: {end_date_formatted}"

            self._log.info(f"Downloading {asset.symbol} | {times} | Progress: {progress:.2f}%")

        try:
            gateway = asset.gateway
            gateway.get_klines(
                symbol=asset.symbol,
                timeframe="1m",
                from_date=int(download_from_date.timestamp()),
                to_date=int(download_to_date.timestamp()),
                callback=_process_klines,
            )

        except Exception as e:
            self._log.error(f"Error downloading data for {self._asset.symbol}: {e}")
            if not klines:
                raise

        if not klines:
            return

        if self._should_restore_ticks or not parquet_file.exists():
            self._save_ticks_with_timeline(klines, parquet_file, download_from_date, download_to_date)
        else:
            self._merge_ticks(klines, parquet_file)

    def _generate_timeline(
        self,
        from_date: datetime.datetime,
        to_date: datetime.datetime,
    ) -> List[int]:
        timestamps: List[int] = []
        current_timestamp = int(from_date.timestamp())
        end_timestamp = int(to_date.timestamp())

        while current_timestamp <= end_timestamp:
            timestamps.append(current_timestamp)
            current_timestamp += self._SECONDS_PER_MINUTE

        return timestamps

    def _get_datetime_from_timestamp(self, timestamp: int) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(timestamp, tz=TIMEZONE)

    def _get_download_start_date(self, parquet_file: Path) -> datetime.datetime:
        assert self._asset is not None
        date = self._TIMELINE_START_DATE

        if self._should_restore_ticks:
            if parquet_file.exists():
                parquet_file.unlink()

            return date

        if parquet_file.exists():
            existing_ticks = polars.scan_parquet(parquet_file)  # pyright: ignore[reportUnknownMemberType]
            last_tick = existing_ticks.select(polars.col("timestamp").max()).collect()
            last_timestamp = last_tick[0, "timestamp"]
            date = self._get_datetime_from_timestamp(last_timestamp)

            self._log.info(f"Resuming download from {date}")
            return date

        self._log.info("No existing data found, starting fresh download")
        return date

    def _get_formatted_timestamp(self, timestamp: int) -> str:
        return self._get_datetime_from_timestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")

    def _get_parquet_path(self, symbol: str) -> Path:
        return self._ticks_folder / f"{symbol}.parquet"

    def _klines_to_dataframe(self, klines: List[GatewayKlineModel]) -> polars.DataFrame:
        data = {
            "timestamp": [kline.open_time for kline in klines],
            "open": [kline.open_price for kline in klines],
            "high": [kline.high_price for kline in klines],
            "low": [kline.low_price for kline in klines],
            "close": [kline.close_price for kline in klines],
            "volume": [kline.volume for kline in klines],
        }

        return polars.DataFrame(data)

    def _load_assets_arrays(
        self,
        symbols: List[str],
        from_date: datetime.datetime,
        to_date: datetime.datetime,
    ) -> Dict[str, List[Optional[float]]]:
        """Load close prices as native Python lists for direct index access."""
        assets_arrays: Dict[str, List[Optional[float]]] = {}
        from_timestamp = int(from_date.timestamp())
        to_timestamp = int(to_date.timestamp())

        for symbol in symbols:
            parquet_path = self._get_parquet_path(symbol)

            if not parquet_path.exists():
                self._log.warning(f"No parquet file for {symbol}")
                continue

            dataframe = (
                polars.scan_parquet(parquet_path)  # pyright: ignore[reportUnknownMemberType]
                .filter((polars.col("timestamp") >= from_timestamp) & (polars.col("timestamp") <= to_timestamp))
                .select("close")
                .collect()
            )

            assets_arrays[symbol] = dataframe["close"].to_list()
            self._log.info(f"Loaded {len(assets_arrays[symbol]):,} rows for {symbol}")

        return assets_arrays

    def _merge_ticks(
        self,
        klines: List[GatewayKlineModel],
        parquet_file: Path,
    ) -> None:
        new_ticks = self._klines_to_dataframe(klines)
        existing_ticks = polars.read_parquet(parquet_file)

        combined_ticks = polars.concat([existing_ticks, new_ticks])
        combined_ticks = combined_ticks.unique(subset=["timestamp"]).sort("timestamp")
        self._atomic_write_parquet(combined_ticks, parquet_file)

        self._report(parquet_file)

    def _report(self, parquet_file: Path) -> None:
        final_ticks = polars.read_parquet(parquet_file)
        actual_start_date = self._get_datetime_from_timestamp(final_ticks[0, "timestamp"])
        actual_end_date = self._get_datetime_from_timestamp(final_ticks[-1, "timestamp"])

        non_null_count = final_ticks.filter(polars.col("close").is_not_null()).height

        self._log.info(f"Data saved to {parquet_file}")
        self._log.info(f"Total rows: {final_ticks.height}")
        self._log.info(f"Rows with data: {non_null_count}")
        self._log.info(f"Actual date range: {actual_start_date} to {actual_end_date}")

    def _save_ticks_ohlcv(
        self,
        klines: List[GatewayKlineModel],
        parquet_file: Path,
    ) -> None:
        new_ticks = self._klines_to_dataframe(klines)
        new_ticks = new_ticks.sort("timestamp")
        self._atomic_write_parquet(new_ticks, parquet_file)

    def _save_ticks_with_timeline(
        self,
        klines: List[GatewayKlineModel],
        parquet_file: Path,
        from_date: datetime.datetime,
        to_date: datetime.datetime,
    ) -> None:
        timeline = self._generate_timeline(from_date, to_date)
        timeline_df = polars.DataFrame({"timestamp": timeline})
        klines_df = self._klines_to_dataframe(klines)
        aligned_df = timeline_df.join(klines_df, on="timestamp", how="left")
        aligned_df = aligned_df.sort("timestamp")
        self._atomic_write_parquet(aligned_df, parquet_file)

        self._report(parquet_file)

    @staticmethod
    def download_parallel(
        tasks: List[DownloadTask],
        on_complete: Optional[Callable[[str], None]] = None,
        on_all_complete: Optional[Callable[[], None]] = None,
    ) -> Dict[str, "TicksService"]:
        """Download tick data for multiple assets in parallel.

        Args:
            tasks: List of DownloadTask with asset and restore_ticks flag.
            on_complete: Callback called when each asset download completes.
            on_all_complete: Callback called when all downloads are complete.

        Returns:
            Dictionary mapping symbol to configured TicksService instance.
        """
        logger = LoggingService()
        tick_services_by_symbol: Dict[str, TicksService] = {}
        services_lock = Lock()
        completed_count = 0
        completed_lock = Lock()
        total_tasks_count = len(tasks)

        def _download_asset(task: DownloadTask) -> Tuple[str, TicksService]:
            nonlocal completed_count
            symbol = task.asset.symbol
            tick_service = TicksService()

            tick_service.setup(
                asset=task.asset,
                restore_ticks=task.restore_ticks,
            )

            with services_lock:
                tick_services_by_symbol[symbol] = tick_service

            if on_complete:
                on_complete(symbol)

            with completed_lock:
                completed_count += 1
                logger.info(f"Download complete for {symbol} ({completed_count}/{total_tasks_count})")

                if completed_count == total_tasks_count and on_all_complete:
                    on_all_complete()

            return symbol, tick_service

        logger.info(f"Starting parallel download for {total_tasks_count} assets")

        with ThreadPoolExecutor(max_workers=total_tasks_count) as executor:
            download_futures = [executor.submit(_download_asset, task) for task in tasks]

            for future in as_completed(download_futures):
                try:
                    future.result()
                except Exception as download_error:
                    logger.error(f"Download failed: {download_error}")

        return tick_services_by_symbol

    @property
    def folder(self) -> Path:
        """Return the folder path for tick data storage."""
        return self._ticks_folder
