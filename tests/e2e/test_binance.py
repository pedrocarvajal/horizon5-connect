import datetime
import unittest
from typing import Any, Dict, List

from configs.timezone import TIMEZONE
from services.gateway import GatewayService
from services.logging import LoggingService


class TestBinance(unittest.TestCase):
    _log: LoggingService

    def setUp(self) -> None:
        self._log = LoggingService()
        self._log.setup("test_binance")

    def test_get_klines(self) -> None:
        gateway = GatewayService("binance")
        all_klines: List[Dict[str, Any]] = []

        def callback(klines: List[Dict[str, Any]]) -> None:
            self._log.info(f"Received {len(klines)} klines")
            all_klines.extend(klines)

        gateway.get_klines(
            futures=True,
            symbol="btcusdt",
            timeframe="1d",
            from_date=datetime.datetime(2024, 1, 1, tzinfo=TIMEZONE).timestamp(),
            to_date=datetime.datetime(2024, 1, 2, tzinfo=TIMEZONE).timestamp(),
            callback=callback,
        )

        self.assertGreater(len(all_klines), 0, "Should return at least 1 kline")
        self._log.info(f"Total klines received: {len(all_klines)}")
