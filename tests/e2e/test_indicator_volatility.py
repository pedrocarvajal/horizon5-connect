import datetime
from typing import Any

from configs.timezone import TIMEZONE
from enums.timeframe import Timeframe
from indicators.volatility import VolatilityIndicator
from services.logging import LoggingService
from tests.e2e.wrappers.indicator import WrapperIndicator


class TestIndicatorVolatility(WrapperIndicator):
    expected_total_candles = 8759
    expected_last_candles = 10
    price_tolerance = 0.0001

    _log: LoggingService

    def setUp(self, **kwargs: Any) -> None:
        super().setUp(
            **kwargs,
            **{"test_name": "test_indicator_volatility"},
        )

        self._log = LoggingService()
        self._log.setup("test_indicator_volatility")

    def test_indicator_volatility(self) -> None:
        candles = self.candles(
            timeframe=Timeframe.ONE_HOUR,
            from_date=datetime.datetime(2024, 1, 1, tzinfo=TIMEZONE),
            to_date=datetime.datetime(2024, 12, 31, tzinfo=TIMEZONE),
            indicators=[
                VolatilityIndicator(
                    key="vol20",
                    window_size=20,
                    price_to_use="close_price",
                ),
            ],
        )

        expected_values = self.get_json_data("indicator_volatility_expected.json")
        last_10_candles = candles[-self.expected_last_candles :]

        assert len(candles) == self.expected_total_candles
        assert len(last_10_candles) == self.expected_last_candles

        for candle, expected in zip(last_10_candles, expected_values, strict=True):
            assert "i" in candle
            assert "vol20" in candle["i"]

            candle_close_price = candle["close_price"]
            expected_close_price = expected["close"]
            vol20_value = candle["i"]["vol20"]["value"]
            expected_vol20_value = expected["vol20"]

            assert abs(candle_close_price - expected_close_price) < 0.01
            assert abs(vol20_value - expected_vol20_value) < self.price_tolerance
