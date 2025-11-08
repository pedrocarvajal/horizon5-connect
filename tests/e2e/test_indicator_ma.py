import datetime
from typing import Any

from configs.timezone import TIMEZONE
from enums.timeframe import Timeframe
from indicators.ma import MAIndicator
from services.logging import LoggingService
from tests.e2e.wrappers.indicator import WrapperIndicator


class TestIndicatorMA(WrapperIndicator):
    expected_total_candles = 8759
    expected_last_candles = 10
    price_tolerance = 0.01

    _log: LoggingService

    def setUp(self, **kwargs: Any) -> None:
        super().setUp(
            **kwargs,
            **{"test_name": "test_indicator_ma"},
        )

        self._log = LoggingService()
        self._log.setup("test_indicator_ma")

    def test_indicator_ma(self) -> None:
        candles = self.candles(
            timeframe=Timeframe.ONE_HOUR,
            from_date=datetime.datetime(2024, 1, 1, tzinfo=TIMEZONE),
            to_date=datetime.datetime(2024, 12, 31, tzinfo=TIMEZONE),
            indicators=[
                MAIndicator(
                    key="sma5",
                    period=5,
                    price_to_use="close_price",
                    exponential=False,
                ),
                MAIndicator(
                    key="ema5",
                    period=5,
                    price_to_use="close_price",
                    exponential=True,
                ),
            ],
        )

        expected_values = self.get_json_data("indicator_ma_expected.json")
        last_10_candles = candles[-self.expected_last_candles :]

        assert len(candles) == self.expected_total_candles
        assert len(last_10_candles) == self.expected_last_candles

        for candle, expected in zip(last_10_candles, expected_values, strict=True):
            assert "i" in candle
            assert "sma5" in candle["i"]
            assert "ema5" in candle["i"]

            candle_close_price = candle["close_price"]
            expected_close_price = expected["close"]
            sma5_value = candle["i"]["sma5"]["value"]
            ema5_value = candle["i"]["ema5"]["value"]
            expected_sma5_value = expected["sma5"]
            expected_ema5_value = expected["ema5"]

            assert abs(candle_close_price - expected_close_price) < self.price_tolerance
            assert abs(sma5_value - expected_sma5_value) < self.price_tolerance
            assert abs(ema5_value - expected_ema5_value) < self.price_tolerance
