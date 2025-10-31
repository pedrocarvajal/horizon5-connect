from collections.abc import Callable
from typing import Dict, List, Optional

from enums.timeframe import Timeframe
from models.candlestick import CandlestickModel
from models.tick import TickModel


class CandleInterface:
    _timeframe: Timeframe
    _candles: Dict[Timeframe, CandlestickModel]
    _on_close: Optional[Callable[[CandlestickModel], None]]

    def on_tick(self, tick: TickModel) -> None:
        pass

    @property
    def candles(self) -> List[CandlestickModel]:
        return self._candles
