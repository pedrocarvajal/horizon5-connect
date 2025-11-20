# Last coding review: 2025-11-18 13:40:00

import datetime
from typing import List

from configs.timezone import TIMEZONE
from services.gateway.models.gateway_kline import GatewayKlineModel
from tests.integration.binance.wrappers.binance import BinanceWrapper


class TestBinanceKline(BinanceWrapper):
    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def setUp(self) -> None:
        super().setUp()
        self._log.setup(name="test_binance_kline")

    def test_get_klines(self) -> None:
        self._log.info("Getting klines for BTCUSDT")

        all_klines: List[GatewayKlineModel] = []

        def callback(klines: List[GatewayKlineModel]) -> None:
            self._log.info(f"Received {len(klines)} klines")
            all_klines.extend(klines)

        self._gateway.get_klines(
            symbol="BTCUSDT",
            timeframe="1d",
            from_date=datetime.datetime(2024, 1, 1, tzinfo=TIMEZONE).timestamp(),
            to_date=datetime.datetime(2024, 1, 2, tzinfo=TIMEZONE).timestamp(),
            callback=callback,
        )

        assert len(all_klines) > 0, f"Should return at least 1 kline, got {len(all_klines)}"
        assert all(isinstance(k, GatewayKlineModel) for k in all_klines), "All klines should be GatewayKlineModel"
        assert all_klines[0].symbol == "BTCUSDT", f"Symbol should be BTCUSDT, got {all_klines[0].symbol}"
        assert all_klines[0].open_time > 0, f"Open time should be > 0, got {all_klines[0].open_time}"
        assert all_klines[0].close_time > 0, f"Close time should be > 0, got {all_klines[0].close_time}"
        assert all_klines[0].open_price > 0, f"Open price should be > 0, got {all_klines[0].open_price}"
        assert all_klines[0].high_price > 0, f"High price should be > 0, got {all_klines[0].high_price}"
        assert all_klines[0].low_price > 0, f"Low price should be > 0, got {all_klines[0].low_price}"
        assert all_klines[0].close_price > 0, f"Close price should be > 0, got {all_klines[0].close_price}"
        assert all_klines[0].volume >= 0, f"Volume should be >= 0, got {all_klines[0].volume}"
        assert all_klines[0].response is not None, "Response should not be None"

        self._log.info(f"Total klines received: {len(all_klines)}")
