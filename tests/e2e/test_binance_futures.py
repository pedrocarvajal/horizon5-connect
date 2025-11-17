import datetime
import unittest
from typing import List

from configs.timezone import TIMEZONE
from services.gateway import GatewayService
from services.gateway.models.gateway_kline import GatewayKlineModel
from services.gateway.models.gateway_symbol_info import GatewaySymbolInfoModel
from services.gateway.models.gateway_trading_fees import GatewayTradingFeesModel
from services.logging import LoggingService


class TestBinanceFutures(unittest.TestCase):
    _log: LoggingService

    def setUp(self) -> None:
        self._log = LoggingService()
        self._log.setup("test_binance_futures")

    def test_get_klines(self) -> None:
        gateway = GatewayService("binance", futures=True)
        all_klines: List[GatewayKlineModel] = []

        def callback(klines: List[GatewayKlineModel]) -> None:
            self._log.info(f"Received {len(klines)} klines")
            all_klines.extend(klines)

        gateway.get_klines(
            symbol="btcusdt",
            timeframe="1d",
            from_date=datetime.datetime(2024, 1, 1, tzinfo=TIMEZONE).timestamp(),
            to_date=datetime.datetime(2024, 1, 2, tzinfo=TIMEZONE).timestamp(),
            callback=callback,
        )

        assert len(all_klines) > 0, "Should return at least 1 kline"
        assert all(isinstance(k, GatewayKlineModel) for k in all_klines), "Wrong type returned."
        self._log.info(f"Total klines received: {len(all_klines)}")
        self._log.info(f"First kline: {all_klines[0]}")

    def test_get_symbol_info(self) -> None:
        gateway = GatewayService("binance", futures=True)
        symbol_info = gateway.get_symbol_info(symbol="btcusdt")

        assert isinstance(symbol_info, GatewaySymbolInfoModel), "Wrong type returned."
        self._log.info(f"Symbol info: {symbol_info}")

    def test_get_trading_fees(self) -> None:
        gateway = GatewayService("binance", futures=True)
        trading_fees = gateway.get_trading_fees(symbol="btcusdt")

        assert isinstance(trading_fees, GatewayTradingFeesModel), "Wrong type returned."
        self._log.info(f"Trading fees: {trading_fees}")

    def test_get_leverage_info(self) -> None:
        gateway = GatewayService("binance", futures=True)
        leverage_info = gateway.get_leverage_info(symbol="btcusdt")

        assert leverage_info is not None, "Wrong type returned."
        assert isinstance(leverage_info, dict), "Wrong type returned."
        self._log.info(f"Leverage info: {leverage_info}")
