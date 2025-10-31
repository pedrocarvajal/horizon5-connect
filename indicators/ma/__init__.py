import datetime

from interfaces.indicator import IndicatorInterface
from models.candlestick import CandlestickModel
from models.tick import TickModel
from services.logging import LoggingService

from .models.value import MAValueModel


class MAIndicator(IndicatorInterface):
    _name: str = "Moving Average"
    _period: int
    _price_to_use: str
    _exponential: bool
    _candles: list[CandlestickModel]
    _values: list[MAValueModel]
    _updated_at: datetime.datetime | None = None

    def __init__(
        self,
        period: int = 5,
        price_to_use: str = "close_price",
        exponential: bool = False,
        candles: list[CandlestickModel] | None = None,
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
        candles = self._candles

        if len(candles) < self._period:
            return

        last_closed_candle = candles[-2]
        last_closed_candle_date = last_closed_candle.kline_close_time

        if self._updated_at is None or self._updated_at < last_closed_candle_date:
            self._updated_at = last_closed_candle_date
            self.refresh()

    def refresh(self) -> None:
        prices = [
            getattr(k, self._price_to_use)
            for k in self._candles[-self._period - 1 : -1]
        ]
        value = MAValueModel()

        if len(prices) < self._period:
            return

        value.date = self._candles[-2].kline_close_time

        if self._exponential:
            if len(self._values) == 0:
                value.value = self._compute_exponential(prices)
            else:
                multiplier = 2 / (self._period + 1)
                current_price = getattr(self._candles[-2], self._price_to_use)
                value.value = (current_price * multiplier) + (
                    self._values[-1].value * (1 - multiplier)
                )
        else:
            value.value = self._compute_simple(prices)

        self._values.append(value)

    def _compute_exponential(self, prices: list[float]) -> float:
        multiplier = 2 / (self._period + 1)
        ema = prices[0]

        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))

        return ema

    def _compute_simple(self, prices: list[float]) -> float:
        return sum(prices) / len(prices)
