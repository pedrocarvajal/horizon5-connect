import datetime

from indicators.donchian_channel import DonchianChannelIndicator
from vendor.configs.timezone import TIMEZONE
from vendor.enums.timeframe import Timeframe
from vendor.services.logging import LoggingService
from vendor.tests.e2e.wrappers.indicator import WrapperIndicator


class TestIndicatorDonchianChannel(WrapperIndicator):
    _EXPECTED_TOTAL_CANDLES: int = 744
    _EXPECTED_LAST_CANDLES: int = 10
    _PRICE_TOLERANCE: float = 0.01

    def __init__(self, method_name: str = "runTest") -> None:
        super().__init__(method_name)

        self._log: LoggingService

    def setUp(self) -> None:
        super().setUp()

        self._log = LoggingService()

    def test_indicator_donchian_channel(self) -> None:
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
                DonchianChannelIndicator(
                    key="donchian20",
                    period=20,
                ),
            ],
        )
        expected_values = self.get_json_data("indicator_donchian_channel_expected.json")
        last_10_candles = candles[-self._EXPECTED_LAST_CANDLES :]

        assert len(candles) == self._EXPECTED_TOTAL_CANDLES
        assert len(last_10_candles) == self._EXPECTED_LAST_CANDLES

        for candle, expected in zip(
            last_10_candles,
            expected_values,
            strict=True,
        ):
            assert "donchian20" in candle.indicators

            candle_close_price = candle.close_price
            expected_close_price = expected["close"]
            donchian_upper = candle.indicators["donchian20"]["upper"]
            donchian_lower = candle.indicators["donchian20"]["lower"]
            donchian_middle = candle.indicators["donchian20"]["middle"]
            expected_upper = expected["donchian_upper"]
            expected_lower = expected["donchian_lower"]
            expected_middle = expected["donchian_middle"]

            assert abs(candle_close_price - expected_close_price) < self._PRICE_TOLERANCE
            assert abs(donchian_upper - expected_upper) < self._PRICE_TOLERANCE
            assert abs(donchian_lower - expected_lower) < self._PRICE_TOLERANCE
            assert abs(donchian_middle - expected_middle) < self._PRICE_TOLERANCE
