from typing import Any

from configs.candles import MAX_CANDLES_IN_MEMORY
from enums.timeframe import Timeframe
from models.candlestick import CandlestickModel
from models.tick import TickModel
from services.logging import LoggingService


class CandleHandler:
    _started: bool
    _max_candles_in_memory: int
    _timeframes: list[Timeframe]
    _candlesticks: dict[Timeframe, list[CandlestickModel]]

    def __init__(self) -> None:
        self._candlesticks = {}
        self._max_candles_in_memory = MAX_CANDLES_IN_MEMORY
        self._started = False

        self._log = LoggingService()
        self._log.setup("candles_handler")

    def setup(self, _timeframes: list[Timeframe], **kwargs: Any) -> None:
        self._asset = kwargs.get("asset")
        self._timeframes = _timeframes

        if self._asset is None:
            raise ValueError("Asset is required")

        for timeframe in _timeframes:
            self._candlesticks[timeframe] = []

        self._log.info(f"Setup {_timeframes} timeframes")

    def on_tick(self, tick: TickModel) -> None:
        pass

    def on_end(self) -> None:
        pass
