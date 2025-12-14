import datetime

from vendor.configs.timezone import TIMEZONE
from vendor.enums.timeframe import Timeframe
from vendor.indicators.ma import MAIndicator
from vendor.services.logging import LoggingService
from vendor.tests.e2e.wrappers.indicator import WrapperIndicator


class TestIndicatorMA(WrapperIndicator):
    _EXPECTED_TOTAL_CANDLES: int = 744
    _EXPECTED_LAST_CANDLES: int = 10
    _PRICE_TOLERANCE: float = 0.01

    def __init__(self, method_name: str = "runTest") -> None:
        super().__init__(method_name)

        self._log: LoggingService

    def setUp(self) -> None:
        super().setUp()

        self._log = LoggingService()

    def test_indicator_ma(self) -> None:
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
                MAIndicator(
                    key="sma5",
                    period=5,
                    price_to_use="close_price",
                    is_exponential=False,
                ),
                MAIndicator(
                    key="ema5",
                    period=5,
                    price_to_use="close_price",
                    is_exponential=True,
                ),
            ],
        )
        expected_values = self.get_json_data("indicator_ma_expected.json")
        last_10_candles = candles[-self._EXPECTED_LAST_CANDLES :]

        assert len(candles) == self._EXPECTED_TOTAL_CANDLES
        assert len(last_10_candles) == self._EXPECTED_LAST_CANDLES

        for candle, expected in zip(
            last_10_candles,
            expected_values,
            strict=True,
        ):
            assert "sma5" in candle.indicators
            assert "ema5" in candle.indicators

            candle_close_price = candle.close_price
            expected_close_price = expected["close"]
            sma5_value = candle.indicators["sma5"]["value"]
            ema5_value = candle.indicators["ema5"]["value"]
            expected_sma5_value = expected["sma5"]
            expected_ema5_value = expected["ema5"]

            assert abs(candle_close_price - expected_close_price) < self._PRICE_TOLERANCE
            assert abs(sma5_value - expected_sma5_value) < self._PRICE_TOLERANCE
            assert abs(ema5_value - expected_ema5_value) < self._PRICE_TOLERANCE
