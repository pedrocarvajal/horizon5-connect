"""Integration tests for MetaAPI kline retrieval."""

import datetime
from typing import List

from vendor.configs.timezone import TIMEZONE
from vendor.services.gateway.models.gateway_kline import GatewayKlineModel
from vendor.tests.integration.metaapi.wrappers.metaapi import MetaApiWrapper


class TestMetaApiKline(MetaApiWrapper):
    """Integration tests for MetaAPI kline operations."""

    def setUp(self) -> None:
        """Set up the test environment."""
        super().setUp()

    def test_get_klines_1m_3days(self) -> None:
        """Test retrieving 3 days of 1-minute klines for XAUUSD."""
        self._log.info("Getting 3 days of 1m klines for XAUUSD")
        all_klines: List[GatewayKlineModel] = []

        def callback(klines: List[GatewayKlineModel]) -> None:
            self._log.info(f"Received {len(klines)} klines, total: {len(all_klines) + len(klines)}")
            all_klines.extend(klines)

        from_date = datetime.datetime(2024, 12, 1, tzinfo=TIMEZONE)
        to_date = datetime.datetime(2024, 12, 4, tzinfo=TIMEZONE)

        self._gateway.get_klines(
            symbol="XAUUSD",
            timeframe="1m",
            from_date=int(from_date.timestamp()),
            to_date=int(to_date.timestamp()),
            callback=callback,
        )

        assert len(all_klines) > 0, f"Should return at least 1 kline, got {len(all_klines)}"
        assert all(isinstance(kline, GatewayKlineModel) for kline in all_klines), (
            "All klines should be GatewayKlineModel"
        )

        first_kline = all_klines[0]
        assert first_kline.symbol == "XAUUSD", f"Symbol should be XAUUSD, got {first_kline.symbol}"
        assert first_kline.source == "metaapi", f"Source should be metaapi, got {first_kline.source}"
        assert first_kline.open_time > 0, f"Open time should be > 0, got {first_kline.open_time}"
        assert first_kline.close_time > 0, f"Close time should be > 0, got {first_kline.close_time}"
        assert first_kline.open_price > 0, f"Open price should be > 0, got {first_kline.open_price}"
        assert first_kline.high_price > 0, f"High price should be > 0, got {first_kline.high_price}"
        assert first_kline.low_price > 0, f"Low price should be > 0, got {first_kline.low_price}"
        assert first_kline.close_price > 0, f"Close price should be > 0, got {first_kline.close_price}"
        assert first_kline.volume >= 0, f"Volume should be >= 0, got {first_kline.volume}"
        assert first_kline.response is not None, "Response should not be None"

        self._log.info(f"Total 1m klines received: {len(all_klines)}")
