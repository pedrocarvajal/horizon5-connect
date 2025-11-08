import datetime
from typing import Any

from configs.timezone import TIMEZONE
from enums.timeframe import Timeframe
from indicators.price_velocity import PriceVelocityIndicator
from services.logging import LoggingService
from tests.e2e.wrappers.indicator import WrapperIndicator


class TestIndicatorPriceVelocity(WrapperIndicator):
    expected_total_candles = 8759
    expected_last_candles = 10
    price_tolerance = 0.01

    _log: LoggingService

    def setUp(self, **kwargs: Any) -> None:
        super().setUp(
            **kwargs,
            **{"test_name": "test_indicator_price_velocity"},
        )

        self._log = LoggingService()
        self._log.setup("test_indicator_price_velocity")

    def test_indicator_price_velocity(self) -> None:
        candles = self.candles(
            timeframe=Timeframe.ONE_HOUR,
            from_date=datetime.datetime(2024, 1, 1, tzinfo=TIMEZONE),
            to_date=datetime.datetime(2024, 12, 31, tzinfo=TIMEZONE),
            indicators=[
                PriceVelocityIndicator(
                    key="pv5",
                    window_size=5,
                    price_to_use="close_price",
                ),
            ],
        )

        expected_values = self.get_json_data("indicator_price_velocity_expected.json")
        last_10_candles = candles[-self.expected_last_candles :]

        assert len(candles) == self.expected_total_candles
        assert len(last_10_candles) == self.expected_last_candles

        for candle, expected in zip(last_10_candles, expected_values, strict=True):
            assert "i" in candle
            assert "pv5" in candle["i"]

            candle_close_price = candle["close_price"]
            expected_close_price = expected["close"]
            pv5_value = candle["i"]["pv5"]["value"]
            expected_pv5_value = expected["pv5"]

            assert abs(candle_close_price - expected_close_price) < self.price_tolerance
            assert abs(pv5_value - expected_pv5_value) < self.price_tolerance
