import datetime

from configs.timezone import TIMEZONE
from enums.timeframe import Timeframe
from indicators.volatility import VolatilityIndicator
from services.logging import LoggingService
from tests.e2e.wrappers.indicator import WrapperIndicator


class TestIndicatorVolatility(WrapperIndicator):
    _EXPECTED_TOTAL_CANDLES: int = 743
    _EXPECTED_LAST_CANDLES: int = 10
    _PRICE_TOLERANCE: float = 0.0001

    def __init__(self, method_name: str = "runTest") -> None:
        super().__init__(method_name)

        self._log: LoggingService

    def setUp(self) -> None:
        super().setUp()

        self._log = LoggingService()
        self._log.setup("test_indicator_volatility")

    def test_indicator_volatility(self) -> None:
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
                VolatilityIndicator(
                    key="vol20",
                    window_size=20,
                    price_to_use="close_price",
                ),
            ],
        )
        expected_values = self.get_json_data("indicator_volatility_expected.json")
        last_10_candles = candles[-self._EXPECTED_LAST_CANDLES :]

        assert len(candles) == self._EXPECTED_TOTAL_CANDLES
        assert len(last_10_candles) == self._EXPECTED_LAST_CANDLES

        for candle, expected in zip(
            last_10_candles,
            expected_values,
            strict=True,
        ):
            assert "i" in candle
            assert "vol20" in candle["i"]

            candle_close_price = candle["close_price"]
            expected_close_price = expected["close"]
            vol20_value = candle["i"]["vol20"]["value"]
            expected_vol20_value = expected["vol20"]

            assert abs(candle_close_price - expected_close_price) < self._PRICE_TOLERANCE
            assert abs(vol20_value - expected_vol20_value) < self._PRICE_TOLERANCE
