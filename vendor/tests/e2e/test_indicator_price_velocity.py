import datetime

from vendor.configs.timezone import TIMEZONE
from vendor.enums.timeframe import Timeframe
from vendor.indicators.price_velocity import PriceVelocityIndicator
from vendor.services.logging import LoggingService
from vendor.tests.e2e.wrappers.indicator import WrapperIndicator


class TestIndicatorPriceVelocity(WrapperIndicator):
    _EXPECTED_TOTAL_CANDLES: int = 743
    _EXPECTED_LAST_CANDLES: int = 10
    _PRICE_TOLERANCE: float = 0.01

    def __init__(self, method_name: str = "runTest") -> None:
        super().__init__(method_name)

        self._log: LoggingService

    def setUp(self) -> None:
        super().setUp()

        self._log = LoggingService()

    def test_indicator_price_velocity(self) -> None:
        candles = self.candles(
            timeframe=Timeframe.ONE_HOUR,
            from_date=datetime.datetime(
                2024,
                1,
                1,
                tzinfo=TIMEZONE,
            ),
            to_date=datetime.datetime(
                2024,
                2,
                1,
                tzinfo=TIMEZONE,
            ),
            indicators=[
                PriceVelocityIndicator(
                    key="pv5",
                    window_size=5,
                    price_to_use="close_price",
                ),
            ],
        )
        expected_values = self.get_json_data("indicator_price_velocity_expected.json")
        last_10_candles = candles[-self._EXPECTED_LAST_CANDLES :]

        assert len(candles) == self._EXPECTED_TOTAL_CANDLES
        assert len(last_10_candles) == self._EXPECTED_LAST_CANDLES

        for candle, expected in zip(
            last_10_candles,
            expected_values,
            strict=True,
        ):
            assert "pv5" in candle.indicators

            candle_close_price = candle.close_price
            expected_close_price = expected["close"]
            pv5_value = candle.indicators["pv5"]["value"]
            expected_pv5_value = expected["pv5"]

            assert abs(candle_close_price - expected_close_price) < self._PRICE_TOLERANCE
            assert abs(pv5_value - expected_pv5_value) < self._PRICE_TOLERANCE
