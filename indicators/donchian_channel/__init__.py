"""Donchian Channel indicator implementation."""

import datetime
from typing import List, Optional

from interfaces.indicator import IndicatorInterface
from models.candle import CandleModel
from models.tick import TickModel
from services.logging import LoggingService

from .models.value import DonchianChannelValueModel


class DonchianChannelIndicator(IndicatorInterface):
    """Donchian Channel indicator for breakout detection and trailing stops."""

    _NAME: str = "Donchian Channel"

    _key: str
    _period: int
    _candles: List[CandleModel]
    _values: List[DonchianChannelValueModel]

    _log: LoggingService

    def __init__(
        self,
        key: str,
        period: int = 20,
        candles: Optional[List[CandleModel]] = None,
    ) -> None:
        """Initialize the Donchian Channel indicator with configuration parameters."""
        self._key = key
        self._period = period
        self._candles = candles if candles is not None else []
        self._values = []

        self._log = LoggingService()

    def on_tick(self, tick: TickModel) -> None:
        """Process incoming tick and refresh indicator if candle closed."""
        super().on_tick(tick)

        if len(self._candles) < self._period:
            return

        if (
            len(self._candles) > 0
            and tick.date >= self._candles[-1].close_time
            and self._should_refresh(self._candles[-1].close_time)
        ):
            self.refresh()

    def refresh(self) -> None:
        """Recalculate the Donchian Channel values based on current candles."""
        if len(self._candles) < self._period:
            return

        window_candles = self._candles[-self._period :]

        if len(window_candles) < self._period:
            return

        upper = max(candle.high_price for candle in window_candles)
        lower = min(candle.low_price for candle in window_candles)
        middle = (upper + lower) / 2

        donchian_value = DonchianChannelValueModel()
        donchian_value.date = self._candles[-1].close_time
        donchian_value.upper = upper
        donchian_value.lower = lower
        donchian_value.middle = middle

        self._values.append(donchian_value)

    def _should_refresh(self, candle_close_time: datetime.datetime) -> bool:
        if len(self._values) == 0:
            return True

        last_date = self._values[-1].date
        return last_date is None or last_date < candle_close_time

    @property
    def values(self) -> List[DonchianChannelValueModel]:
        """Return the list of calculated Donchian Channel values."""
        return self._values

    @property
    def upper(self) -> Optional[float]:
        """Return the current upper band value."""
        if len(self._values) == 0:
            return None
        return self._values[-1].upper

    @property
    def lower(self) -> Optional[float]:
        """Return the current lower band value."""
        if len(self._values) == 0:
            return None
        return self._values[-1].lower

    @property
    def middle(self) -> Optional[float]:
        """Return the current middle band value."""
        if len(self._values) == 0:
            return None
        return self._values[-1].middle
