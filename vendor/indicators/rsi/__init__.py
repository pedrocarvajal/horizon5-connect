"""Relative Strength Index (RSI) indicator implementation."""

import datetime
from typing import List, Optional

from vendor.interfaces.indicator import IndicatorInterface
from vendor.models.candle import CandleModel
from vendor.models.tick import TickModel
from vendor.services.logging import LoggingService

from .models.value import RSIValueModel


class RSIIndicator(IndicatorInterface):
    """RSI indicator for measuring momentum and overbought/oversold conditions."""

    _NAME: str = "Relative Strength Index"
    _MIN_CANDLES_REQUIRED: int = 2

    _key: str
    _period: int
    _price_to_use: str
    _candles: List[CandleModel]
    _values: List[RSIValueModel]
    _gains: List[float]
    _losses: List[float]
    _avg_gain: float
    _avg_loss: float

    _log: LoggingService

    def __init__(
        self,
        key: str,
        period: int = 14,
        price_to_use: str = "close_price",
        candles: Optional[List[CandleModel]] = None,
    ) -> None:
        """Initialize the RSI indicator with configuration parameters."""
        self._key = key
        self._period = period
        self._price_to_use = price_to_use
        self._candles = candles if candles is not None else []
        self._values = []
        self._gains = []
        self._losses = []
        self._avg_gain = 0.0
        self._avg_loss = 0.0

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
        """Recalculate the RSI value based on current candles using RMA smoothing."""
        if len(self._candles) < self._MIN_CANDLES_REQUIRED:
            return

        current_candle = self._candles[-1]
        previous_candle = self._candles[-2]

        current_price = getattr(current_candle, self._price_to_use)
        previous_price = getattr(previous_candle, self._price_to_use)

        change = current_price - previous_price
        gain = max(change, 0.0)
        loss = abs(min(change, 0.0))

        self._gains.append(gain)
        self._losses.append(loss)

        rsi_value = RSIValueModel()
        rsi_value.date = current_candle.close_time

        if len(self._gains) < self._period:
            rsi_value.value = 0.0
        elif len(self._gains) == self._period:
            self._avg_gain = sum(self._gains) / self._period
            self._avg_loss = sum(self._losses) / self._period

            if self._avg_loss == 0:
                rsi_value.value = 100.0
            else:
                relative_strength = self._avg_gain / self._avg_loss
                rsi_value.value = 100.0 - (100.0 / (1.0 + relative_strength))
        else:
            alpha = 1.0 / self._period
            self._avg_gain = (alpha * gain) + ((1 - alpha) * self._avg_gain)
            self._avg_loss = (alpha * loss) + ((1 - alpha) * self._avg_loss)

            if self._avg_loss == 0:
                rsi_value.value = 100.0
            else:
                relative_strength = self._avg_gain / self._avg_loss
                rsi_value.value = 100.0 - (100.0 / (1.0 + relative_strength))

        self._values.append(rsi_value)

    def _should_refresh(self, candle_close_time: datetime.datetime) -> bool:
        if len(self._values) == 0:
            return True

        last_date = self._values[-1].date
        return last_date is None or last_date < candle_close_time

    @property
    def values(self) -> List[RSIValueModel]:
        """Return the list of calculated RSI values."""
        return self._values

    @property
    def value(self) -> Optional[float]:
        """Return the current RSI value."""
        if len(self._values) == 0:
            return None
        return self._values[-1].value
