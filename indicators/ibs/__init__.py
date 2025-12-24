"""Internal Bar Strength (IBS) indicator implementation."""

import datetime
from typing import List, Optional

from vendor.interfaces.indicator import IndicatorInterface
from vendor.interfaces.logging import LoggingInterface
from vendor.models.candle import CandleModel
from vendor.models.tick import TickModel
from vendor.services.logging import LoggingService

from .models.value import IBSValueModel


class IBSIndicator(IndicatorInterface):
    """IBS indicator for measuring where price closed within the daily range.

    IBS = (Close - Low) / (High - Low)

    Values range from 0 to 1:
    - 0 = closed at daily low (oversold)
    - 1 = closed at daily high (overbought)
    - Below 0.25 = potential buy signal (mean reversion)
    - Above 0.75 = potential sell signal (mean reversion)
    """

    _NAME: str = "Internal Bar Strength"
    _MIN_CANDLES_REQUIRED: int = 1

    _key: str
    _candles: List[CandleModel]
    _values: List[IBSValueModel]

    _log: LoggingInterface

    def __init__(
        self,
        key: str,
        candles: Optional[List[CandleModel]] = None,
    ) -> None:
        """Initialize the IBS indicator."""
        self._key = key
        self._candles = candles if candles is not None else []
        self._values = []

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
        """Recalculate the IBS value based on current candle."""
        if len(self._candles) < self._MIN_CANDLES_REQUIRED:
            return

        current_candle = self._candles[-1]

        high_price = current_candle.high_price
        low_price = current_candle.low_price
        close_price = current_candle.close_price

        ibs_value = IBSValueModel()
        ibs_value.date = current_candle.close_time

        price_range = high_price - low_price
        if price_range == 0:
            ibs_value.value = 0.5
        else:
            ibs_value.value = (close_price - low_price) / price_range

        self._values.append(ibs_value)

    def _should_refresh(self, candle_close_time: datetime.datetime) -> bool:
        if len(self._values) == 0:
            return True

        last_date = self._values[-1].date
        return last_date is None or last_date < candle_close_time

    @property
    def values(self) -> List[IBSValueModel]:
        """Return the list of calculated IBS values."""
        return self._values

    @property
    def value(self) -> Optional[float]:
        """Return the current IBS value."""
        if len(self._values) == 0:
            return None
        return self._values[-1].value
