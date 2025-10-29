from typing import Any

from configs.candles import MAX_CANDLES_IN_MEMORY
from enums.timeframe import Timeframe
from models.candlestick import CandlestickModel
from models.tick import TickModel
from services.logging import LoggingService


class CandleHandler:
    _max_candles_in_memory: int
    _timeframes: list[Timeframe]
    _candlesticks: dict[Timeframe, list[CandlestickModel]]

    def __init__(self) -> None:
        self._candlesticks = {}
        self._max_candles_in_memory = MAX_CANDLES_IN_MEMORY

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
        # for timeframe in self._timeframes:
        #     if not self._candlesticks[timeframe]:
        #         self._candlesticks[timeframe] = []

        #     if len(self._candlesticks[timeframe]) == 0:
        #         candle = CandlestickModel()
        #         candle.source = self._asset.gateway.gateway_name
        #         candle.symbol = self._asset.symbol
        #         candle.kline_open_time = tick.date.timestamp() * 1000
        #         candle.open_price = tick.price
        #         candle.high_price = tick.price
        #         candle.low_price = tick.price
        #         candle.close_price = tick.price
        #         candle.volume = 0
        #         candle.kline_close_time = tick.date.timestamp() * 1000

        #         self._candlesticks[timeframe].append(candle)

        #     last_candle = self._candlesticks[timeframe][-1]

        pass

    def on_end(self) -> None:
        pass
