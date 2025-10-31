import datetime
from typing import List, Optional

from interfaces.indicator import IndicatorInterface
from models.candlestick import CandlestickModel
from models.tick import TickModel
from services.logging import LoggingService

from .models.value import MAValueModel


class MAIndicator(IndicatorInterface):
    _MULTIPLIER_COEFFICIENT: int = 2

    _name: str = "Moving Average"
    _period: int
    _price_to_use: str
    _exponential: bool
    _candles: List[CandlestickModel]
    _values: List[MAValueModel]

    def __init__(
        self,
        period: int = 5,
        price_to_use: str = "close_price",
        exponential: bool = False,
        candles: Optional[List[CandlestickModel]] = None,
    ) -> None:
        self._period = period
        self._price_to_use = price_to_use
        self._exponential = exponential
        self._candles = candles if candles is not None else []
        self._values = []

        self._log = LoggingService()
        self._log.setup("ma_indicator")

    def on_tick(self, tick: TickModel) -> None:
        super().on_tick(tick)

        if len(self._candles) < self._period:
            return

        last_closed_candle = self._candles[-2]

        if self._should_refresh(last_closed_candle.kline_close_time):
            self.refresh()

    def refresh(self) -> None:
        prices = [
            getattr(candle, self._price_to_use)
            for candle in self._candles[-self._period - 1 : -1]
        ]

        if len(prices) < self._period:
            return

        value = MAValueModel()
        value.date = self._candles[-2].kline_close_time

        if self._exponential:
            if len(self._values) == 0:
                value.value = self._compute_exponential(prices)
            else:
                multiplier = self._MULTIPLIER_COEFFICIENT / (self._period + 1)
                current_price = getattr(self._candles[-2], self._price_to_use)
                value.value = (current_price * multiplier) + (
                    self._values[-1].value * (1 - multiplier)
                )
        else:
            value.value = self._compute_simple(prices)

        self._values.append(value)

    def _compute_exponential(self, prices: List[float]) -> float:
        multiplier = self._MULTIPLIER_COEFFICIENT / (self._period + 1)
        exponential_moving_average = prices[0]

        for price in prices[1:]:
            exponential_moving_average = (price * multiplier) + (
                exponential_moving_average * (1 - multiplier)
            )

        return exponential_moving_average

    def _compute_simple(self, prices: List[float]) -> float:
        return sum(prices) / len(prices)

    def _should_refresh(self, candle_close_time: datetime.datetime) -> bool:
        if len(self._values) == 0:
            return True

        return self._values[-1].date < candle_close_time
