"""Integration test for comparing broker 1h candles vs system-aggregated 1h candles."""

import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import List, Mapping, Union

import polars

from assets.xauusd import Asset as XAUUSDAsset
from vendor.configs.timezone import TIMEZONE
from vendor.enums.timeframe import Timeframe
from vendor.services.candle import CandleService
from vendor.services.gateway.models.gateway_kline import GatewayKlineModel
from vendor.services.logging import LoggingService
from vendor.services.ticks import TicksService
from vendor.tests.integration.metaapi.wrappers.metaapi import MetaApiWrapper


@dataclass
class AggregatedCandle:
    """Represents an aggregated candle from 1m data."""

    open_time: int
    close_time: int
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float
    minute_count: int = 60


@dataclass
class CandleComparison:
    """Comparison result between broker and aggregated candle."""

    timestamp: int
    datetime_str: str
    broker_open: float
    broker_high: float
    broker_low: float
    broker_close: float
    aggregated_open: float
    aggregated_high: float
    aggregated_low: float
    aggregated_close: float
    diff_open: float
    diff_high: float
    diff_low: float
    diff_close: float


class TestCandleAggregation(MetaApiWrapper):
    """Test comparing broker 1h candles with system-aggregated 1h candles from 1m data."""

    _PARQUET_PATH: Path = Path(__file__).parent.parent.parent.parent / "storage" / "ticks" / "XAUUSD.parquet"
    _PRICE_TOLERANCE: float = 0.50

    def setUp(self) -> None:
        """Set up the test environment."""
        super().setUp()
        self._log = LoggingService()

    def test_compare_1h_candles_september_2024_to_today(self) -> None:
        """Compare broker 1h candles with aggregated 1h candles from September 2024 to today."""
        from_date = datetime.datetime(2024, 9, 1, 0, 0, 0, tzinfo=TIMEZONE)
        now = datetime.datetime.now(tz=TIMEZONE)
        to_date = now.replace(hour=0, minute=0, second=0, microsecond=0)

        self._log.info("=" * 80)
        self._log.info("STEP 1: Downloading 1h candles from broker (MetaAPI)")
        self._log.info("=" * 80)

        broker_candles = self._download_broker_1h_candles(from_date, to_date)
        self._log.info(f"Downloaded {len(broker_candles)} broker 1h candles")

        if not broker_candles:
            self.fail("No broker candles downloaded")

        self._log_sample_broker_candles(broker_candles[:5])

        self._log.info("=" * 80)
        self._log.info("STEP 2: Aggregating 1h candles from parquet 1m data")
        self._log.info("=" * 80)

        aggregated_candles = self._aggregate_1h_candles_from_parquet(from_date, to_date)
        self._log.info(f"Aggregated {len(aggregated_candles)} candles from 1m data")

        if not aggregated_candles:
            self.fail("No aggregated candles created")

        self._log_sample_aggregated_candles(aggregated_candles[:5])

        self._log.info("=" * 80)
        self._log.info("STEP 3: Comparing broker vs aggregated candles")
        self._log.info("=" * 80)

        comparisons = self._compare_candles(broker_candles, aggregated_candles)
        self._log.info(f"Compared {len(comparisons)} matching candles")

        self._log.info("=" * 80)
        self._log.info("STEP 4: Analyzing differences")
        self._log.info("=" * 80)

        self._analyze_differences(comparisons)

        max_diff = max(max(abs(c.diff_open), abs(c.diff_high), abs(c.diff_low), abs(c.diff_close)) for c in comparisons)

        self._log.info(f"Maximum difference found: {max_diff:.4f}")
        self._log.info(f"Tolerance threshold: {self._PRICE_TOLERANCE}")

        assert max_diff < self._PRICE_TOLERANCE, (
            f"Maximum difference {max_diff:.4f} exceeds tolerance {self._PRICE_TOLERANCE}"
        )

    def _download_broker_1h_candles(
        self,
        from_date: datetime.datetime,
        to_date: datetime.datetime,
    ) -> List[GatewayKlineModel]:
        """Download 1h candles directly from broker."""
        all_klines: List[GatewayKlineModel] = []

        def callback(klines: List[GatewayKlineModel]) -> None:
            if klines:
                self._log.info(f"Received batch of {len(klines)} klines, total: {len(all_klines) + len(klines)}")
                all_klines.extend(klines)

        self._gateway.get_klines(
            symbol="XAUUSD",
            timeframe="1h",
            from_date=int(from_date.timestamp()),
            to_date=int(to_date.timestamp()),
            callback=callback,
        )

        return sorted(all_klines, key=lambda k: k.open_time)

    def _aggregate_1h_candles_from_parquet(
        self,
        from_date: datetime.datetime,
        to_date: datetime.datetime,
    ) -> List[AggregatedCandle]:
        """Aggregate 1h candles from 1m parquet data using correct OHLC formula."""
        if not self._PARQUET_PATH.exists():
            self._log.error(f"Parquet file not found: {self._PARQUET_PATH}")
            return []

        from_timestamp = int(from_date.timestamp())
        to_timestamp = int(to_date.timestamp())

        dataframe = polars.read_parquet(self._PARQUET_PATH)
        filtered_dataframe = dataframe.filter(
            (polars.col("timestamp") >= from_timestamp)
            & (polars.col("timestamp") <= to_timestamp)
            & (polars.col("close").is_not_null())
        ).sort("timestamp")

        self._log.info(f"Loaded {filtered_dataframe.height} 1m candles from parquet")

        aggregated_candles: List[AggregatedCandle] = []
        hour_seconds = 3600

        current_hour_start = (from_timestamp // hour_seconds) * hour_seconds
        end_timestamp = to_timestamp

        while current_hour_start < end_timestamp:
            current_hour_end = current_hour_start + hour_seconds

            hour_data = filtered_dataframe.filter(
                (polars.col("timestamp") >= current_hour_start) & (polars.col("timestamp") < current_hour_end)
            )

            if hour_data.height > 0:
                candle = AggregatedCandle(
                    open_time=current_hour_start,
                    close_time=current_hour_end,
                    open_price=hour_data["open"][0],
                    high_price=hour_data["high"].max(),
                    low_price=hour_data["low"].min(),
                    close_price=hour_data["close"][-1],
                    volume=hour_data["volume"].sum(),
                    minute_count=hour_data.height,
                )
                aggregated_candles.append(candle)

            current_hour_start = current_hour_end

        return aggregated_candles

    def _compare_candles(
        self,
        broker_candles: List[GatewayKlineModel],
        aggregated_candles: List[AggregatedCandle],
    ) -> List[CandleComparison]:
        """Compare broker candles with aggregated candles.

        Filters out hours with incomplete 1m data (< 60 candles) since those
        represent broker data gaps, not system aggregation errors.
        """
        broker_by_timestamp = {c.open_time: c for c in broker_candles}
        aggregated_by_timestamp = {c.open_time: c for c in aggregated_candles}

        common_timestamps = set(broker_by_timestamp.keys()) & set(aggregated_by_timestamp.keys())

        incomplete_hours = [ts for ts in common_timestamps if aggregated_by_timestamp[ts].minute_count < 60]

        if incomplete_hours:
            self._log.info(f"Filtering {len(incomplete_hours)} hours with incomplete 1m data (broker gaps)")
            common_timestamps = common_timestamps - set(incomplete_hours)

        self._log.info(f"Found {len(common_timestamps)} common timestamps with complete data")

        comparisons: List[CandleComparison] = []

        for timestamp in sorted(common_timestamps):
            broker = broker_by_timestamp[timestamp]
            aggregated = aggregated_by_timestamp[timestamp]

            dt = datetime.datetime.fromtimestamp(timestamp, tz=TIMEZONE)

            comparison = CandleComparison(
                timestamp=timestamp,
                datetime_str=dt.strftime("%Y-%m-%d %H:%M"),
                broker_open=broker.open_price,
                broker_high=broker.high_price,
                broker_low=broker.low_price,
                broker_close=broker.close_price,
                aggregated_open=aggregated.open_price,
                aggregated_high=aggregated.high_price,
                aggregated_low=aggregated.low_price,
                aggregated_close=aggregated.close_price,
                diff_open=broker.open_price - aggregated.open_price,
                diff_high=broker.high_price - aggregated.high_price,
                diff_low=broker.low_price - aggregated.low_price,
                diff_close=broker.close_price - aggregated.close_price,
            )
            comparisons.append(comparison)

        return comparisons

    def _analyze_differences(self, comparisons: List[CandleComparison]) -> None:
        """Analyze and log the differences between broker and aggregated candles."""
        if not comparisons:
            self._log.warning("No comparisons to analyze")
            return

        diff_opens = [abs(c.diff_open) for c in comparisons]
        diff_highs = [abs(c.diff_high) for c in comparisons]
        diff_lows = [abs(c.diff_low) for c in comparisons]
        diff_closes = [abs(c.diff_close) for c in comparisons]

        self._log.info("Difference Statistics (absolute values):")
        self._log.info(f"  Open  - Max: {max(diff_opens):.4f}, Avg: {sum(diff_opens) / len(diff_opens):.4f}")
        self._log.info(f"  High  - Max: {max(diff_highs):.4f}, Avg: {sum(diff_highs) / len(diff_highs):.4f}")
        self._log.info(f"  Low   - Max: {max(diff_lows):.4f}, Avg: {sum(diff_lows) / len(diff_lows):.4f}")
        self._log.info(f"  Close - Max: {max(diff_closes):.4f}, Avg: {sum(diff_closes) / len(diff_closes):.4f}")

        threshold = 0.1
        outliers = [
            c
            for c in comparisons
            if any(
                [
                    abs(c.diff_open) > threshold,
                    abs(c.diff_high) > threshold,
                    abs(c.diff_low) > threshold,
                    abs(c.diff_close) > threshold,
                ]
            )
        ]

        if outliers:
            self._log.info(f"\nOutliers (diff > {threshold}):")
            for outlier in outliers[:10]:
                outlier_msg = f"  {outlier.datetime_str}: O={outlier.diff_open:+.4f} "
                outlier_msg += f"H={outlier.diff_high:+.4f} L={outlier.diff_low:+.4f} C={outlier.diff_close:+.4f}"
                self._log.info(outlier_msg)

    def _log_sample_broker_candles(self, candles: List[GatewayKlineModel]) -> None:
        """Log sample broker candles for verification."""
        self._log.info("Sample broker candles:")
        for candle in candles:
            dt = datetime.datetime.fromtimestamp(candle.open_time, tz=TIMEZONE)
            candle_msg = f"  {dt.strftime('%Y-%m-%d %H:%M')}: O={candle.open_price:.2f} "
            candle_msg += f"H={candle.high_price:.2f} L={candle.low_price:.2f} C={candle.close_price:.2f}"
            self._log.info(candle_msg)

    def _log_sample_aggregated_candles(self, candles: List[AggregatedCandle]) -> None:
        """Log sample aggregated candles for verification."""
        self._log.info("Sample aggregated candles:")
        for candle in candles:
            dt = datetime.datetime.fromtimestamp(candle.open_time, tz=TIMEZONE)
            candle_msg = f"  {dt.strftime('%Y-%m-%d %H:%M')}: O={candle.open_price:.2f} "
            candle_msg += f"H={candle.high_price:.2f} L={candle.low_price:.2f} C={candle.close_price:.2f}"
            self._log.info(candle_msg)

    def test_corrected_system_vs_broker(self) -> None:
        """Verify the corrected system (TicksService + CandleService) matches broker candles."""
        from_date = datetime.datetime(2024, 9, 1, 0, 0, 0, tzinfo=TIMEZONE)
        to_date = datetime.datetime.now(tz=TIMEZONE)

        self._log.info("=" * 80)
        self._log.info("VERIFYING CORRECTED SYSTEM (TicksService + CandleService)")
        self._log.info("=" * 80)

        self._log.info("\nSTEP 1: Download broker 1h candles (ground truth)")
        broker_candles = self._download_broker_1h_candles(from_date, to_date)
        self._log.info(f"Downloaded {len(broker_candles)} broker candles")

        self._log.info("\nSTEP 2: Generate 1h candles using corrected system")
        system_candles = self._generate_candles_with_corrected_system(from_date, to_date)
        self._log.info(f"Generated {len(system_candles)} system candles")

        self._log.info("\nSTEP 3: Get parquet aggregation to identify incomplete hours")
        parquet_candles = self._aggregate_1h_candles_from_parquet(from_date, to_date)
        incomplete_timestamps = {c.open_time for c in parquet_candles if c.minute_count < 60}
        if incomplete_timestamps:
            self._log.info(f"Found {len(incomplete_timestamps)} hours with incomplete data (broker gaps)")

        self._log.info("\nSTEP 4: Compare broker vs corrected system")

        broker_by_timestamp = {c.open_time: c for c in broker_candles}
        system_by_timestamp = {c.open_time: c for c in system_candles}
        common_timestamps = set(broker_by_timestamp.keys()) & set(system_by_timestamp.keys())
        common_timestamps = sorted(common_timestamps - incomplete_timestamps)

        self._log.info(f"Comparing {len(common_timestamps)} common candles with complete data")

        diff_opens: List[float] = []
        diff_highs: List[float] = []
        diff_lows: List[float] = []
        diff_closes: List[float] = []

        self._log.info("\nSample comparisons (first 10):")
        self._log.info("-" * 100)

        self._log_sample_system_comparisons(common_timestamps[:10], broker_by_timestamp, system_by_timestamp)

        for timestamp in common_timestamps:
            broker = broker_by_timestamp[timestamp]
            system = system_by_timestamp[timestamp]

            diff_opens.append(abs(broker.open_price - system.open_price))
            diff_highs.append(abs(broker.high_price - system.high_price))
            diff_lows.append(abs(broker.low_price - system.low_price))
            diff_closes.append(abs(broker.close_price - system.close_price))

        self._log.info("\n" + "=" * 80)
        self._log.info("CORRECTED SYSTEM RESULTS")
        self._log.info("=" * 80)
        self._log.info(f"Open  diff: Max={max(diff_opens):.4f}, Avg={sum(diff_opens) / len(diff_opens):.4f}")
        self._log.info(f"High  diff: Max={max(diff_highs):.4f}, Avg={sum(diff_highs) / len(diff_highs):.4f}")
        self._log.info(f"Low   diff: Max={max(diff_lows):.4f}, Avg={sum(diff_lows) / len(diff_lows):.4f}")
        self._log.info(f"Close diff: Max={max(diff_closes):.4f}, Avg={sum(diff_closes) / len(diff_closes):.4f}")

        max_diff = max(diff_opens + diff_highs + diff_lows + diff_closes)

        self._log.info(f"\nMaximum difference: {max_diff:.4f}")
        self._log.info(f"Tolerance: {self._PRICE_TOLERANCE}")

        assert max_diff < self._PRICE_TOLERANCE, (
            f"Maximum difference {max_diff:.4f} exceeds tolerance {self._PRICE_TOLERANCE}"
        )

        self._log.info("\nSUCCESS: Corrected system matches broker candles within tolerance!")

    def _log_sample_system_comparisons(
        self,
        timestamps: List[int],
        broker_by_timestamp: Mapping[int, Union[GatewayKlineModel, AggregatedCandle]],
        system_by_timestamp: Mapping[int, Union[GatewayKlineModel, AggregatedCandle]],
    ) -> None:
        """Log sample comparisons between broker and system candles."""
        for timestamp in timestamps:
            broker = broker_by_timestamp[timestamp]
            system = system_by_timestamp[timestamp]
            dt = datetime.datetime.fromtimestamp(timestamp, tz=TIMEZONE)

            d_open = broker.open_price - system.open_price
            d_high = broker.high_price - system.high_price
            d_low = broker.low_price - system.low_price
            d_close = broker.close_price - system.close_price

            broker_str = f"B[{broker.open_price:.2f}/{broker.high_price:.2f}/"
            broker_str += f"{broker.low_price:.2f}/{broker.close_price:.2f}]"
            system_str = f"S[{system.open_price:.2f}/{system.high_price:.2f}/"
            system_str += f"{system.low_price:.2f}/{system.close_price:.2f}]"
            diff_str = f"D[{d_open:+.4f}/{d_high:+.4f}/{d_low:+.4f}/{d_close:+.4f}]"

            self._log.info(f"{dt.strftime('%Y-%m-%d %H:%M')}: {broker_str} {system_str} {diff_str}")

    def _generate_candles_with_corrected_system(
        self,
        from_date: datetime.datetime,
        to_date: datetime.datetime,
    ) -> List[AggregatedCandle]:
        """Generate 1h candles using the corrected TicksService + CandleService."""
        ticks_service = TicksService()
        ticks_service.setup(asset=XAUUSDAsset(), restore_ticks=False, disable_download=True)

        candle_service = CandleService(timeframe=Timeframe.ONE_HOUR)

        ticks = ticks_service.ticks(from_date=from_date, to_date=to_date)
        self._log.info(f"Loaded {len(ticks)} ticks from TicksService")

        if ticks:
            first_tick = ticks[0]
            tick_msg = f"First tick: date={first_tick.date}, close_price={first_tick.close_price}, "
            tick_msg += f"open={first_tick.open_price}, high={first_tick.high_price}, low={first_tick.low_price}"
            self._log.info(tick_msg)

        for tick in ticks:
            candle_service.on_tick(tick)

        candles = candle_service.candles
        self._log.info(f"Generated {len(candles)} candles from CandleService")

        aggregated_candles: List[AggregatedCandle] = []
        for candle in candles:
            aggregated_candles.append(
                AggregatedCandle(
                    open_time=int(candle.open_time.timestamp()),
                    close_time=int(candle.close_time.timestamp()),
                    open_price=candle.open_price,
                    high_price=candle.high_price,
                    low_price=candle.low_price,
                    close_price=candle.close_price,
                    volume=0.0,
                )
            )

        return aggregated_candles

    def test_current_system_error_demonstration(self) -> None:
        """Demonstrate the error in current system that uses only close price as tick."""
        from_date = datetime.datetime(2024, 9, 1, 0, 0, 0, tzinfo=TIMEZONE)
        to_date = datetime.datetime.now(tz=TIMEZONE)

        self._log.info("=" * 80)
        self._log.info("DEMONSTRATING CURRENT SYSTEM ERROR")
        self._log.info("=" * 80)

        self._log.info("\nSTEP 1: Download broker 1h candles (ground truth)")
        broker_candles = self._download_broker_1h_candles(from_date, to_date)

        self._log.info("\nSTEP 2: Simulate current system (aggregating using only close prices)")
        system_candles = self._aggregate_using_only_close(from_date, to_date)

        self._log.info("\nSTEP 3: Compare broker vs current system")

        broker_by_timestamp = {c.open_time: c for c in broker_candles}
        system_by_timestamp = {c.open_time: c for c in system_candles}
        common_timestamps = sorted(set(broker_by_timestamp.keys()) & set(system_by_timestamp.keys()))

        self._log.info(f"Comparing {len(common_timestamps)} candles\n")

        diff_opens: List[float] = []
        diff_highs: List[float] = []
        diff_lows: List[float] = []
        diff_closes: List[float] = []

        self._log.info("Sample comparisons (first 10):")
        self._log.info("-" * 100)

        self._log_sample_system_comparisons(common_timestamps[:10], broker_by_timestamp, system_by_timestamp)

        for timestamp in common_timestamps:
            broker = broker_by_timestamp[timestamp]
            system = system_by_timestamp[timestamp]

            diff_opens.append(abs(broker.open_price - system.open_price))
            diff_highs.append(abs(broker.high_price - system.high_price))
            diff_lows.append(abs(broker.low_price - system.low_price))
            diff_closes.append(abs(broker.close_price - system.close_price))

        self._log_error_summary(diff_opens, diff_highs, diff_lows, diff_closes)

        assert max(diff_highs) > 0.5 or max(diff_lows) > 0.5, (
            "Expected significant differences in high/low prices to demonstrate the bug"
        )

    def _log_error_summary(
        self,
        diff_opens: List[float],
        diff_highs: List[float],
        diff_lows: List[float],
        diff_closes: List[float],
    ) -> None:
        """Log error summary for system comparison."""
        self._log.info("\n" + "=" * 80)
        self._log.info("ERROR SUMMARY - Current System vs Broker")
        self._log.info("=" * 80)
        self._log.info(f"Open  errors: Max={max(diff_opens):.4f}, Avg={sum(diff_opens) / len(diff_opens):.4f}")
        self._log.info(f"High  errors: Max={max(diff_highs):.4f}, Avg={sum(diff_highs) / len(diff_highs):.4f}")
        self._log.info(f"Low   errors: Max={max(diff_lows):.4f}, Avg={sum(diff_lows) / len(diff_lows):.4f}")
        self._log.info(f"Close errors: Max={max(diff_closes):.4f}, Avg={sum(diff_closes) / len(diff_closes):.4f}")

        self._log.info("\nCONCLUSION:")
        self._log.info("- Close prices are identical (expected, since system uses close as tick)")
        self._log.info("- Open prices differ because system uses first close, not first open")
        self._log.info("- High prices differ because system uses max(close), not max(high)")
        self._log.info("- Low prices differ because system uses min(close), not min(low)")

    def _aggregate_using_only_close(
        self,
        from_date: datetime.datetime,
        to_date: datetime.datetime,
    ) -> List[AggregatedCandle]:
        """Simulate current system behavior: aggregate using only close prices as ticks."""
        if not self._PARQUET_PATH.exists():
            return []

        from_timestamp = int(from_date.timestamp())
        to_timestamp = int(to_date.timestamp())

        dataframe = polars.read_parquet(self._PARQUET_PATH)
        filtered_dataframe = dataframe.filter(
            (polars.col("timestamp") >= from_timestamp)
            & (polars.col("timestamp") <= to_timestamp)
            & (polars.col("close").is_not_null())
        ).sort("timestamp")

        aggregated_candles: List[AggregatedCandle] = []
        hour_seconds = 3600

        current_hour_start = (from_timestamp // hour_seconds) * hour_seconds
        end_timestamp = to_timestamp

        while current_hour_start < end_timestamp:
            current_hour_end = current_hour_start + hour_seconds

            hour_data = filtered_dataframe.filter(
                (polars.col("timestamp") >= current_hour_start) & (polars.col("timestamp") < current_hour_end)
            )

            if hour_data.height > 0:
                close_prices = hour_data["close"].to_list()

                candle = AggregatedCandle(
                    open_time=current_hour_start,
                    close_time=current_hour_end,
                    open_price=close_prices[0],
                    high_price=max(close_prices),
                    low_price=min(close_prices),
                    close_price=close_prices[-1],
                    volume=hour_data["volume"].sum(),
                )
                aggregated_candles.append(candle)

            current_hour_start = current_hour_end

        return aggregated_candles
