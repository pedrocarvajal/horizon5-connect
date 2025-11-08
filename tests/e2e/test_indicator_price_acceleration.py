import datetime
from typing import Any

from configs.timezone import TIMEZONE
from enums.timeframe import Timeframe
from indicators.price_acceleration import PriceAccelerationIndicator
from services.logging import LoggingService
from tests.e2e.wrappers.indicator import WrapperIndicator


class TestIndicatorPriceAcceleration(WrapperIndicator):
    expected_total_candles = 8759
    expected_last_candles = 10
    price_tolerance = 0.01

    _log: LoggingService

    def setUp(self, **kwargs: Any) -> None:
        super().setUp(
            **kwargs,
            **{"test_name": "test_indicator_price_acceleration"},
        )

        self._log = LoggingService()
        self._log.setup("test_indicator_price_acceleration")

    def test_indicator_price_acceleration(self) -> None:
        candles = self.candles(
            timeframe=Timeframe.ONE_HOUR,
            from_date=datetime.datetime(2024, 1, 1, tzinfo=TIMEZONE),
            to_date=datetime.datetime(2024, 12, 31, tzinfo=TIMEZONE),
            indicators=[
                PriceAccelerationIndicator(
                    key="pa5",
                    window_size=5,
                    price_to_use="close_price",
                ),
            ],
        )

        expected_values = self.get_json_data("indicator_price_acceleration_expected.json")
        last_10_candles = candles[-self.expected_last_candles :]

        assert len(candles) == self.expected_total_candles
        assert len(last_10_candles) == self.expected_last_candles

        for candle, expected in zip(last_10_candles, expected_values, strict=True):
            assert "i" in candle
            assert "pa5" in candle["i"]

            candle_close_price = candle["close_price"]
            expected_close_price = expected["close"]
            pa5_value = candle["i"]["pa5"]["value"]
            expected_pa5_value = expected["pa5"]

            assert abs(candle_close_price - expected_close_price) < self.price_tolerance
            assert abs(pa5_value - expected_pa5_value) < self.price_tolerance
