from collections.abc import Callable
from datetime import datetime, timedelta
from typing import List, Optional

from enums.timeframe import Timeframe
from interfaces.candle import CandleInterface
from models.candlestick import CandlestickModel
from models.tick import TickModel


class CandleService(CandleInterface):
    def __init__(
        self,
        timeframe: Timeframe,
        on_close: Optional[Callable[[CandlestickModel], None]] = None,
    ) -> None:
        self._timeframe = timeframe
        self._on_close = on_close
        self._candles: List[CandlestickModel] = []

    def on_tick(self, tick: TickModel) -> None:
        self._compute(tick)

    def _compute(self, tick: TickModel) -> None:
        if len(self._candles) == 0 or tick.date >= self._candles[-1].kline_close_time:
            if len(self._candles) > 0 and self._on_close is not None:
                self._on_close(candle=self._candles[-1])

            aligned_time = self._align_time_to_timeframe(tick.date)
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

    def _align_time_to_timeframe(self, date: datetime) -> datetime:
        timeframe_seconds = self._timeframe.to_seconds()

        seconds_in_hour = 3600
        seconds_in_day = 86400

        if timeframe_seconds < seconds_in_hour:
            return self._align_minutes(date, timeframe_seconds)

        if timeframe_seconds < seconds_in_day:
            return self._align_hours(date, timeframe_seconds)

        return self._align_days_or_longer(date, timeframe_seconds)

    def _align_days_or_longer(self, date: datetime, timeframe_seconds: int) -> datetime:
        seconds_in_day = 86400
        seconds_in_three_days = 259200
        seconds_in_week = 604800
        seconds_in_month = 2592000

        if timeframe_seconds == seconds_in_day:
            return date.replace(hour=0, minute=0, second=0, microsecond=0)

        if timeframe_seconds == seconds_in_three_days:
            return self._align_three_days(date)

        if timeframe_seconds == seconds_in_week:
            return self._align_week(date)

        if timeframe_seconds == seconds_in_month:
            return self._align_month(date)

        return date

    def _align_minutes(self, date: datetime, timeframe_seconds: int) -> datetime:
        minutes_interval = timeframe_seconds // 60
        aligned_minute = (date.minute // minutes_interval) * minutes_interval
        return date.replace(minute=aligned_minute, second=0, microsecond=0)

    def _align_hours(self, date: datetime, timeframe_seconds: int) -> datetime:
        hours_interval = timeframe_seconds // 3600
        aligned_hour = (date.hour // hours_interval) * hours_interval
        return date.replace(hour=aligned_hour, minute=0, second=0, microsecond=0)

    def _align_three_days(self, date: datetime) -> datetime:
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        epoch = datetime(1970, 1, 1, tzinfo=start_of_day.tzinfo)
        days_since_epoch = (start_of_day - epoch).days
        aligned_days = (days_since_epoch // 3) * 3
        return epoch + timedelta(days=aligned_days)

    def _align_week(self, date: datetime) -> datetime:
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        days_since_monday = date.weekday()
        return start_of_day - timedelta(days=days_since_monday)

    def _align_month(self, date: datetime) -> datetime:
        return date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    @property
    def candles(self) -> List[CandlestickModel]:
        return self._candles
