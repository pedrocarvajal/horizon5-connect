from interfaces.indicator import IndicatorInterface
from models.candlestick import CandlestickModel
from services.logging import LoggingService

from .models.value import MAValueModel


class MAIndicator(IndicatorInterface):
    _name: str = "Moving Average"
    _period: int
    _exponential: bool
    _candles: list[CandlestickModel]
    _values: list[MAValueModel]

    def __init__(
        self,
        period: int = 5,
        exponential: bool = False,
        candles: list[CandlestickModel] | None = None,
    ) -> None:
        self._period = period
        self._exponential = exponential
        self._candles = candles if candles is not None else []
        self._values = []

        self._log = LoggingService()
        self._log.setup("ma_indicator")

    def refresh(self) -> None:
        prices = [k.close_price for k in self._candles[-self._period :]]
        value = MAValueModel()

        if len(prices) < self._period:
            return

        value.timestamp = self._candles[-1].kline_close_time

        if self._exponential:
            if len(self._values) == 0:
                value.value = self._compute_exponential(prices)
            else:
                multiplier = 2 / (self._period + 1)
                current_price = self._candles[-1].close_price
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
