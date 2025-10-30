from collections.abc import Callable
from datetime import timedelta

from enums.timeframe import Timeframe
from interfaces.candle import CandleInterface
from models.candlestick import CandlestickModel
from models.tick import TickModel


class CandleService(CandleInterface):
    def __init__(
        self,
        timeframe: Timeframe,
        on_close: Callable[[CandlestickModel], None] | None = None,
    ) -> None:
        self._timeframe = timeframe
        self._on_close = on_close
        self._candles: list[CandlestickModel] = []

    def on_tick(self, tick: TickModel) -> None:
        self._compute(tick)

    def _compute(self, tick: TickModel) -> None:
        if len(self._candles) == 0 or tick.date >= self._candles[-1].kline_close_time:
            if len(self._candles) > 0 and self._on_close is not None:
                self._on_close(candle=self._candles[-1])

            aligned_time = tick.date.replace(minute=0, second=0, microsecond=0)
            candle_duration = timedelta(seconds=self._timeframe.to_seconds())

            candle = CandlestickModel()
            candle.kline_open_time = aligned_time
            candle.kline_close_time = aligned_time + candle_duration
            candle.open_price = tick.price
            candle.high_price = tick.price
            candle.low_price = tick.price
            candle.close_price = tick.price

            self._candles.append(candle)

        else:
            candle = self._candles[-1]
            candle.high_price = max(candle.high_price, tick.price)
            candle.low_price = min(candle.low_price, tick.price)
            candle.close_price = tick.price
