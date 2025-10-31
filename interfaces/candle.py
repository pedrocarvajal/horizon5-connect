from collections.abc import Callable

from enums.timeframe import Timeframe
from models.candlestick import CandlestickModel
from models.tick import TickModel


class CandleInterface:
    _timeframe: Timeframe
    _candles: dict[Timeframe, CandlestickModel]
    _on_close: Callable[[CandlestickModel], None] | None

    def on_tick(self, tick: TickModel) -> None:
        pass

    @property
    def candles(self) -> list[CandlestickModel]:
        return self._candles
