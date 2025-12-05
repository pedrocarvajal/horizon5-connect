"""Candle service for building candlesticks from tick data."""

from collections.abc import Callable
from datetime import datetime, timedelta
from typing import List, Optional

from enums.timeframe import Timeframe
from interfaces.candle import CandleInterface
from interfaces.indicator import IndicatorInterface
from models.candle import CandleModel
from models.tick import TickModel


class CandleService(CandleInterface):
    """Service that builds OHLC candlesticks from tick data with indicator support."""

    SECONDS_IN_HOUR = 3600
    SECONDS_IN_DAY = 86400
    SECONDS_IN_THREE_DAYS = 259200
    SECONDS_IN_WEEK = 604800
    SECONDS_IN_MONTH = 2592000

    _timeframe: Timeframe
    _on_close: Optional[Callable[[CandleModel], None]]
    _candles: List[CandleModel]
    _indicators: List[IndicatorInterface]

    def __init__(
        self,
        timeframe: Timeframe,
        on_close: Optional[Callable[[CandleModel], None]] = None,
        indicators: Optional[List[IndicatorInterface]] = None,
    ) -> None:
        """Initialize the candle service with timeframe and optional indicators."""
        self._timeframe = timeframe
        self._on_close = on_close
        self._candles = []
        self._indicators = indicators if indicators is not None else []

        for indicator in self._indicators:
            indicator._candles = self._candles  # pyright: ignore[reportPrivateUsage]

    def on_tick(self, tick: TickModel) -> None:
        """Process incoming tick and update current candle."""
        for indicator in self._indicators:
            indicator.on_tick(tick)

        self._compute(tick)

    def _align_days_or_longer(self, date: datetime, timeframe_seconds: int) -> datetime:
        if timeframe_seconds == self.SECONDS_IN_DAY:
            return date.replace(hour=0, minute=0, second=0, microsecond=0)

        if timeframe_seconds == self.SECONDS_IN_THREE_DAYS:
            return self._align_three_days(date)

        if timeframe_seconds == self.SECONDS_IN_WEEK:
            return self._align_week(date)

        if timeframe_seconds == self.SECONDS_IN_MONTH:
            return self._align_month(date)

        return date

    def _align_hours(self, date: datetime, timeframe_seconds: int) -> datetime:
        hours_interval = timeframe_seconds // self.SECONDS_IN_HOUR
        aligned_hour = (date.hour // hours_interval) * hours_interval
        return date.replace(hour=aligned_hour, minute=0, second=0, microsecond=0)

    def _align_minutes(self, date: datetime, timeframe_seconds: int) -> datetime:
        minutes_interval = timeframe_seconds // 60
        aligned_minute = (date.minute // minutes_interval) * minutes_interval
        return date.replace(minute=aligned_minute, second=0, microsecond=0)

    def _align_month(self, date: datetime) -> datetime:
        return date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    def _align_three_days(self, date: datetime) -> datetime:
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        epoch = datetime(1970, 1, 1, tzinfo=start_of_day.tzinfo)
        days_since_epoch = (start_of_day - epoch).days
        aligned_days = (days_since_epoch // 3) * 3
        return epoch + timedelta(days=aligned_days)

    def _align_time_to_timeframe(self, date: datetime) -> datetime:
        timeframe_seconds = self._timeframe.to_seconds()

        if timeframe_seconds < self.SECONDS_IN_HOUR:
            return self._align_minutes(date, timeframe_seconds)

        if timeframe_seconds < self.SECONDS_IN_DAY:
            return self._align_hours(date, timeframe_seconds)

        return self._align_days_or_longer(date, timeframe_seconds)

    def _align_week(self, date: datetime) -> datetime:
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        days_since_monday = date.weekday()
        return start_of_day - timedelta(days=days_since_monday)

    def _attach_indicators_to_candle(self, candle: CandleModel) -> None:
        candle.indicators = {}

        for indicator in self._indicators:
            if len(indicator.values) > 0:
                latest_value = indicator.values[-1]

                if latest_value.date == candle.close_time:
                    candle.indicators[indicator.key] = latest_value.to_dict()

    def _compute(self, tick: TickModel) -> None:
        if len(self._candles) == 0 or tick.date >= self._candles[-1].close_time:
            if len(self._candles) > 0:
                self._attach_indicators_to_candle(self._candles[-1])

                if self._on_close is not None:
                    self._on_close(self._candles[-1])

            aligned_time = self._align_time_to_timeframe(tick.date)
            candle_duration = timedelta(seconds=self._timeframe.to_seconds())
            candle = CandleModel(
                open_time=aligned_time,
                close_time=aligned_time + candle_duration,
                open_price=tick.price,
                high_price=tick.price,
                low_price=tick.price,
                close_price=tick.price,
                indicators={},
            )

            self._candles.append(candle)

        else:
            candle = self._candles[-1]
            candle.high_price = max(candle.high_price, tick.price)
            candle.low_price = min(candle.low_price, tick.price)
            candle.close_price = tick.price

    @property
    def candles(self) -> List[CandleModel]:
        """Return completed candles excluding the current in-progress candle."""
        return self._candles[0:-1]
