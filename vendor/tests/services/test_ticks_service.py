"""Integration tests for TicksService with real MetaAPI data."""

# pyright: reportPrivateUsage=false

import datetime
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Callable, List

import polars

from vendor.configs.timezone import TIMEZONE
from vendor.services.gateway import GatewayService
from vendor.services.gateway.models.gateway_kline import GatewayKlineModel
from vendor.services.logging import LoggingService
from vendor.services.ticks import TicksService


@unittest.skip("Tests require MetaAPI credentials - run manually when testing gateway integration")
class TestTicksServiceIntegration(unittest.TestCase):
    """Integration tests for TicksService downloading real data from MetaAPI."""

    _SYMBOL: str = "XAUUSD"
    _temp_dir: str = ""
    _service: TicksService  # pyright: ignore[reportUninitializedInstanceVariable]
    _gateway: GatewayService  # pyright: ignore[reportUninitializedInstanceVariable]
    _log: LoggingService  # pyright: ignore[reportUninitializedInstanceVariable]

    def setUp(self) -> None:
        self._temp_dir = tempfile.mkdtemp()
        self._log = LoggingService()
        self._gateway = GatewayService(gateway="metaapi", backtest=True)
        self._service = TicksService()
        self._service._ticks_folder = Path(self._temp_dir)

    def tearDown(self) -> None:
        shutil.rmtree(self._temp_dir, ignore_errors=True)

    def test_download_klines_from_metaapi(self) -> None:
        """Test downloading klines directly from MetaAPI gateway."""
        all_klines: List[GatewayKlineModel] = []
        from_date = datetime.datetime(2024, 1, 1, 0, 0, 0, tzinfo=TIMEZONE)
        to_date = datetime.datetime(2024, 1, 1, 1, 0, 0, tzinfo=TIMEZONE)

        def callback(klines: List[GatewayKlineModel]) -> None:
            all_klines.extend(klines)

        self._gateway.get_klines(
            symbol=self._SYMBOL,
            timeframe="1m",
            from_date=int(from_date.timestamp()),
            to_date=int(to_date.timestamp()),
            callback=callback,
        )

        assert len(all_klines) > 0, "Should download at least 1 kline"
        self._log.info(f"Downloaded {len(all_klines)} klines from MetaAPI")

        for kline in all_klines:
            assert kline.open_price > 0, f"Open price should be > 0, got {kline.open_price}"
            assert kline.high_price > 0, f"High price should be > 0, got {kline.high_price}"
            assert kline.low_price > 0, f"Low price should be > 0, got {kline.low_price}"
            assert kline.close_price > 0, f"Close price should be > 0, got {kline.close_price}"
            assert kline.volume >= 0, f"Volume should be >= 0, got {kline.volume}"

    def test_save_klines_with_ohlcv_format(self) -> None:
        """Test saving klines in OHLCV parquet format."""
        all_klines: List[GatewayKlineModel] = []
        from_date = datetime.datetime(2024, 1, 1, 0, 0, 0, tzinfo=TIMEZONE)
        to_date = datetime.datetime(2024, 1, 1, 0, 30, 0, tzinfo=TIMEZONE)

        def callback(klines: List[GatewayKlineModel]) -> None:
            all_klines.extend(klines)

        self._gateway.get_klines(
            symbol=self._SYMBOL,
            timeframe="1m",
            from_date=int(from_date.timestamp()),
            to_date=int(to_date.timestamp()),
            callback=callback,
        )

        parquet_file = Path(self._temp_dir) / f"{self._SYMBOL}.parquet"
        self._service._save_ticks_ohlcv(all_klines, parquet_file)

        assert parquet_file.exists(), "Parquet file should be created"

        dataframe = polars.read_parquet(parquet_file)
        expected_columns = ["timestamp", "open", "high", "low", "close", "volume"]
        assert dataframe.columns == expected_columns, f"Columns should be {expected_columns}"
        assert dataframe.height == len(all_klines), "Row count should match kline count"

        self._log.info(f"Saved {dataframe.height} rows to {parquet_file}")

    def test_save_klines_with_timeline_creates_complete_timeline(self) -> None:
        """Test saving klines aligned to timeline creates gaps with null."""
        all_klines: List[GatewayKlineModel] = []
        from_date = datetime.datetime(2024, 1, 1, 0, 0, 0, tzinfo=TIMEZONE)
        to_date = datetime.datetime(2024, 1, 1, 0, 10, 0, tzinfo=TIMEZONE)

        def callback(klines: List[GatewayKlineModel]) -> None:
            all_klines.extend(klines)

        self._gateway.get_klines(
            symbol=self._SYMBOL,
            timeframe="1m",
            from_date=int(from_date.timestamp()),
            to_date=int(to_date.timestamp()),
            callback=callback,
        )

        parquet_file = Path(self._temp_dir) / f"{self._SYMBOL}.parquet"
        self._service._save_ticks_with_timeline(all_klines, parquet_file, from_date, to_date)

        dataframe = polars.read_parquet(parquet_file)

        expected_rows = 11
        assert dataframe.height == expected_rows, f"Should have {expected_rows} rows (11 minutes)"

        timestamps = dataframe["timestamp"].to_list()
        assert timestamps == sorted(timestamps), "Timestamps should be sorted"

        first_timestamp = int(from_date.timestamp())
        last_timestamp = int(to_date.timestamp())
        assert timestamps[0] == first_timestamp, f"First timestamp should be {first_timestamp}"
        assert timestamps[-1] == last_timestamp, f"Last timestamp should be {last_timestamp}"

        self._log.info(f"Timeline created with {dataframe.height} rows")

    def test_read_ticks_from_saved_parquet(self) -> None:
        """Test reading ticks from saved OHLCV parquet file."""
        all_klines: List[GatewayKlineModel] = []
        from_date = datetime.datetime(2024, 1, 1, 0, 0, 0, tzinfo=TIMEZONE)
        to_date = datetime.datetime(2024, 1, 1, 0, 10, 0, tzinfo=TIMEZONE)

        def callback(klines: List[GatewayKlineModel]) -> None:
            all_klines.extend(klines)

        self._gateway.get_klines(
            symbol=self._SYMBOL,
            timeframe="1m",
            from_date=int(from_date.timestamp()),
            to_date=int(to_date.timestamp()),
            callback=callback,
        )

        parquet_file = Path(self._temp_dir) / f"{self._SYMBOL}.parquet"
        self._service._save_ticks_with_timeline(all_klines, parquet_file, from_date, to_date)
        self._service._asset = type("Asset", (), {"symbol": self._SYMBOL})()  # type: ignore[assignment]

        ticks = self._service.ticks(from_date, to_date)

        assert len(ticks) > 0, "Should return ticks"

        for tick in ticks:
            assert tick.close_price > 0, f"Close price should be > 0, got {tick.close_price}"
            assert tick.is_simulated is True, "Ticks should be marked as simulated"
            assert from_date <= tick.date <= to_date, f"Tick date {tick.date} should be in range"

        self._log.info(f"Read {len(ticks)} ticks from parquet")

    def test_merge_new_klines_with_existing_data(self) -> None:
        """Test merging new downloaded klines with existing parquet data."""
        first_klines: List[GatewayKlineModel] = []
        first_from = datetime.datetime(2024, 1, 1, 0, 0, 0, tzinfo=TIMEZONE)
        first_to = datetime.datetime(2024, 1, 1, 0, 5, 0, tzinfo=TIMEZONE)

        def callback_first(klines: List[GatewayKlineModel]) -> None:
            first_klines.extend(klines)

        self._gateway.get_klines(
            symbol=self._SYMBOL,
            timeframe="1m",
            from_date=int(first_from.timestamp()),
            to_date=int(first_to.timestamp()),
            callback=callback_first,
        )

        parquet_file = Path(self._temp_dir) / f"{self._SYMBOL}.parquet"
        self._service._save_ticks_ohlcv(first_klines, parquet_file)

        initial_count = polars.read_parquet(parquet_file).height

        second_klines: List[GatewayKlineModel] = []
        second_from = datetime.datetime(2024, 1, 1, 0, 3, 0, tzinfo=TIMEZONE)
        second_to = datetime.datetime(2024, 1, 1, 0, 10, 0, tzinfo=TIMEZONE)

        def callback_second(klines: List[GatewayKlineModel]) -> None:
            second_klines.extend(klines)

        self._gateway.get_klines(
            symbol=self._SYMBOL,
            timeframe="1m",
            from_date=int(second_from.timestamp()),
            to_date=int(second_to.timestamp()),
            callback=callback_second,
        )

        self._service._merge_ticks(second_klines, parquet_file)

        final_df = polars.read_parquet(parquet_file)
        final_count = final_df.height

        assert final_count > initial_count, f"Should have more rows after merge ({final_count} > {initial_count})"

        timestamps = final_df["timestamp"].to_list()
        assert len(timestamps) == len(set(timestamps)), "Should have no duplicate timestamps"
        assert timestamps == sorted(timestamps), "Timestamps should be sorted"

        self._log.info(f"Merged data: {initial_count} -> {final_count} rows")

    def test_parquet_file_path_format(self) -> None:
        """Test that parquet file path follows new format: SYMBOL.parquet."""
        path = self._service._get_parquet_path(self._SYMBOL)

        assert path.name == f"{self._SYMBOL}.parquet", f"File name should be {self._SYMBOL}.parquet"
        assert path.suffix == ".parquet", "File extension should be .parquet"

    def test_timeline_generation_accuracy(self) -> None:
        """Test timeline generation produces correct minute intervals."""
        from_date = datetime.datetime(2024, 1, 1, 0, 0, 0, tzinfo=TIMEZONE)
        to_date = datetime.datetime(2024, 1, 1, 1, 0, 0, tzinfo=TIMEZONE)

        timeline = self._service._generate_timeline(from_date, to_date)

        assert len(timeline) == 61, "1 hour should have 61 minute timestamps (inclusive)"

        for i in range(1, len(timeline)):
            diff = timeline[i] - timeline[i - 1]
            assert diff == 60, f"Interval should be 60 seconds, got {diff}"

        assert timeline[0] == int(from_date.timestamp()), "First timestamp should match from_date"
        assert timeline[-1] == int(to_date.timestamp()), "Last timestamp should match to_date"

    def test_klines_ohlcv_values_are_valid(self) -> None:
        """Test that downloaded OHLCV values follow market data rules."""
        all_klines: List[GatewayKlineModel] = []
        from_date = datetime.datetime(2024, 1, 1, 0, 0, 0, tzinfo=TIMEZONE)
        to_date = datetime.datetime(2024, 1, 1, 0, 30, 0, tzinfo=TIMEZONE)

        def callback(klines: List[GatewayKlineModel]) -> None:
            all_klines.extend(klines)

        self._gateway.get_klines(
            symbol=self._SYMBOL,
            timeframe="1m",
            from_date=int(from_date.timestamp()),
            to_date=int(to_date.timestamp()),
            callback=callback,
        )

        for kline in all_klines:
            assert kline.high_price >= kline.low_price, "High should be >= Low"
            assert kline.high_price >= kline.open_price, "High should be >= Open"
            assert kline.high_price >= kline.close_price, "High should be >= Close"
            assert kline.low_price <= kline.open_price, "Low should be <= Open"
            assert kline.low_price <= kline.close_price, "Low should be <= Close"

        self._log.info(f"Validated {len(all_klines)} klines OHLCV rules")

    def test_get_timeline_returns_correct_timestamps(self) -> None:
        """Test get_timeline public method returns correct timestamps."""
        from_date = datetime.datetime(2024, 1, 1, 0, 0, 0, tzinfo=TIMEZONE)
        to_date = datetime.datetime(2024, 1, 1, 0, 10, 0, tzinfo=TIMEZONE)

        timeline = self._service.get_timeline(from_date, to_date)

        assert len(timeline) == 11, "Should have 11 timestamps (0-10 minutes inclusive)"
        assert timeline[0] == int(from_date.timestamp()), "First timestamp should match from_date"
        assert timeline[-1] == int(to_date.timestamp()), "Last timestamp should match to_date"

        for i in range(1, len(timeline)):
            diff = timeline[i] - timeline[i - 1]
            assert diff == 60, f"Interval should be 60 seconds, got {diff}"

    def test_load_assets_data_returns_dataframes(self) -> None:
        """Test load_assets_data loads parquet files into DataFrames."""
        all_klines: List[GatewayKlineModel] = []
        from_date = datetime.datetime(2024, 1, 1, 0, 0, 0, tzinfo=TIMEZONE)
        to_date = datetime.datetime(2024, 1, 1, 0, 10, 0, tzinfo=TIMEZONE)

        def callback(klines: List[GatewayKlineModel]) -> None:
            all_klines.extend(klines)

        self._gateway.get_klines(
            symbol=self._SYMBOL,
            timeframe="1m",
            from_date=int(from_date.timestamp()),
            to_date=int(to_date.timestamp()),
            callback=callback,
        )

        parquet_file = Path(self._temp_dir) / f"{self._SYMBOL}.parquet"
        self._service._save_ticks_with_timeline(all_klines, parquet_file, from_date, to_date)

        assets_data = self._service.load_assets_data([self._SYMBOL], from_date, to_date)

        assert self._SYMBOL in assets_data, f"Should contain data for {self._SYMBOL}"
        assert assets_data[self._SYMBOL].height == 11, "Should have 11 rows"
        assert "timestamp" in assets_data[self._SYMBOL].columns, "Should have timestamp column"
        assert "close" in assets_data[self._SYMBOL].columns, "Should have close column"

        self._log.info(f"Loaded {assets_data[self._SYMBOL].height} rows for {self._SYMBOL}")

    def test_load_assets_data_handles_missing_symbol(self) -> None:
        """Test load_assets_data handles missing symbols gracefully."""
        from_date = datetime.datetime(2024, 1, 1, 0, 0, 0, tzinfo=TIMEZONE)
        to_date = datetime.datetime(2024, 1, 1, 0, 10, 0, tzinfo=TIMEZONE)

        assets_data = self._service.load_assets_data(["NONEXISTENT"], from_date, to_date)

        assert len(assets_data) == 0, "Should return empty dict for missing symbol"

    def test_load_assets_data_filters_by_date_range(self) -> None:
        """Test load_assets_data only returns data within date range."""
        all_klines: List[GatewayKlineModel] = []
        save_from = datetime.datetime(2024, 1, 1, 0, 0, 0, tzinfo=TIMEZONE)
        save_to = datetime.datetime(2024, 1, 1, 0, 30, 0, tzinfo=TIMEZONE)

        def callback(klines: List[GatewayKlineModel]) -> None:
            all_klines.extend(klines)

        self._gateway.get_klines(
            symbol=self._SYMBOL,
            timeframe="1m",
            from_date=int(save_from.timestamp()),
            to_date=int(save_to.timestamp()),
            callback=callback,
        )

        parquet_file = Path(self._temp_dir) / f"{self._SYMBOL}.parquet"
        self._service._save_ticks_with_timeline(all_klines, parquet_file, save_from, save_to)

        query_from = datetime.datetime(2024, 1, 1, 0, 10, 0, tzinfo=TIMEZONE)
        query_to = datetime.datetime(2024, 1, 1, 0, 20, 0, tzinfo=TIMEZONE)

        assets_data = self._service.load_assets_data([self._SYMBOL], query_from, query_to)

        assert self._SYMBOL in assets_data, f"Should contain data for {self._SYMBOL}"
        assert assets_data[self._SYMBOL].height == 11, "Should have 11 rows (10-20 minutes inclusive)"

        timestamps = assets_data[self._SYMBOL]["timestamp"].to_list()
        assert min(timestamps) >= int(query_from.timestamp()), "Min timestamp should be >= query_from"
        assert max(timestamps) <= int(query_to.timestamp()), "Max timestamp should be <= query_to"

    def test_iterate_ticks_yields_tick_models(self) -> None:
        """Test iterate_ticks yields tuples of (datetime, Dict[symbol, TickModel])."""
        all_klines: List[GatewayKlineModel] = []
        from_date = datetime.datetime(2024, 1, 1, 0, 0, 0, tzinfo=TIMEZONE)
        to_date = datetime.datetime(2024, 1, 1, 0, 5, 0, tzinfo=TIMEZONE)

        def callback(klines: List[GatewayKlineModel]) -> None:
            all_klines.extend(klines)

        self._gateway.get_klines(
            symbol=self._SYMBOL,
            timeframe="1m",
            from_date=int(from_date.timestamp()),
            to_date=int(to_date.timestamp()),
            callback=callback,
        )

        parquet_file = Path(self._temp_dir) / f"{self._SYMBOL}.parquet"
        self._service._save_ticks_with_timeline(all_klines, parquet_file, from_date, to_date)

        ticks_count = 0
        for tick_date, ticks_dict in self._service.iterate_ticks([self._SYMBOL], from_date, to_date):
            ticks_count += 1

            assert isinstance(tick_date, datetime.datetime), "First element should be datetime"
            assert isinstance(ticks_dict, dict), "Second element should be dict"

            if self._SYMBOL in ticks_dict:
                tick = ticks_dict[self._SYMBOL]
                assert tick.close_price > 0, f"Close price should be > 0, got {tick.close_price}"
                assert tick.is_simulated is True, "Should be marked as simulated"
                assert tick.date == tick_date, "Tick date should match iteration date"

        assert ticks_count == 6, "Should iterate over 6 timestamps (0-5 minutes inclusive)"
        self._log.info(f"Iterated over {ticks_count} ticks")

    def test_iterate_ticks_handles_multiple_symbols(self) -> None:
        """Test iterate_ticks handles multiple symbols correctly."""
        symbols = ["XAUUSD", "GBPUSD"]
        from_date = datetime.datetime(2024, 1, 1, 0, 0, 0, tzinfo=TIMEZONE)
        to_date = datetime.datetime(2024, 1, 1, 0, 5, 0, tzinfo=TIMEZONE)

        for symbol in symbols:
            all_klines: List[GatewayKlineModel] = []

            def make_callback(
                klines_list: List[GatewayKlineModel],
            ) -> Callable[[List[GatewayKlineModel]], None]:
                def callback(klines: List[GatewayKlineModel]) -> None:
                    klines_list.extend(klines)

                return callback

            self._gateway.get_klines(
                symbol=symbol,
                timeframe="1m",
                from_date=int(from_date.timestamp()),
                to_date=int(to_date.timestamp()),
                callback=make_callback(all_klines),
            )

            parquet_file = Path(self._temp_dir) / f"{symbol}.parquet"
            self._service._save_ticks_with_timeline(all_klines, parquet_file, from_date, to_date)

        ticks_with_both = 0
        for _tick_date, ticks_dict in self._service.iterate_ticks(symbols, from_date, to_date):
            if "XAUUSD" in ticks_dict and "GBPUSD" in ticks_dict:
                ticks_with_both += 1

        assert ticks_with_both > 0, "Should have at least one tick with both symbols"
        self._log.info(f"Found {ticks_with_both} ticks with both symbols")
