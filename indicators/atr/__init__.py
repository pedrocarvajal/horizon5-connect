"""Average True Range (ATR) indicator implementation."""

import datetime
from typing import List, Optional

from vendor.interfaces.indicator import IndicatorInterface
from vendor.models.candle import CandleModel
from vendor.models.tick import TickModel
from vendor.services.logging import LoggingService

from .models.value import ATRValueModel


class ATRIndicator(IndicatorInterface):
    """ATR indicator for measuring market volatility using RMA smoothing."""

    _NAME: str = "Average True Range"
    _MIN_CANDLES_REQUIRED: int = 2

    _key: str
    _period: int
    _candles: List[CandleModel]
    _values: List[ATRValueModel]
    _true_ranges: List[float]

    _log: LoggingService

    def __init__(
        self,
        key: str,
        period: int = 14,
        candles: Optional[List[CandleModel]] = None,
    ) -> None:
        """Initialize the ATR indicator with configuration parameters."""
        self._key = key
        self._period = period
        self._candles = candles if candles is not None else []
        self._values = []
        self._true_ranges = []

        self._log = LoggingService()

    def on_tick(self, tick: TickModel) -> None:
        """Process incoming tick and refresh indicator if candle closed."""
        super().on_tick(tick)

        if len(self._candles) < self._MIN_CANDLES_REQUIRED:
            return

        if (
            len(self._candles) > 0
            and tick.date >= self._candles[-1].close_time
            and self._should_refresh(self._candles[-1].close_time)
        ):
            self.refresh()

    def refresh(self) -> None:
        """Recalculate the ATR value based on current candles using RMA."""
        if len(self._candles) < self._MIN_CANDLES_REQUIRED:
            return

        current_candle = self._candles[-1]
        previous_candle = self._candles[-2]

        true_range = self._calculate_true_range(current_candle, previous_candle)
        self._true_ranges.append(true_range)

        atr_value = ATRValueModel()
        atr_value.date = current_candle.close_time

        if len(self._true_ranges) < self._period:
            atr_value.value = 0.0
        elif len(self._true_ranges) == self._period:
            atr_value.value = sum(self._true_ranges) / self._period
        else:
            previous_atr = self._values[-1].value if self._values else 0.0
            alpha = 1 / self._period
            atr_value.value = (alpha * true_range) + ((1 - alpha) * previous_atr)

        self._values.append(atr_value)

    def _calculate_true_range(self, current: CandleModel, previous: CandleModel) -> float:
        high_low = current.high_price - current.low_price
        high_close = abs(current.high_price - previous.close_price)
        low_close = abs(current.low_price - previous.close_price)
        return max(high_low, high_close, low_close)

    def _should_refresh(self, candle_close_time: datetime.datetime) -> bool:
        if len(self._values) == 0:
            return True

        last_date = self._values[-1].date
        return last_date is None or last_date < candle_close_time

    @property
    def values(self) -> List[ATRValueModel]:
        """Return the list of calculated ATR values."""
        return self._values

    @property
    def value(self) -> Optional[float]:
        """Return the current ATR value."""
        if len(self._values) == 0:
            return None
        return self._values[-1].value
