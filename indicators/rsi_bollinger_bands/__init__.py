"""RSI Bollinger Bands indicator implementation."""

import datetime
import math
from typing import List, Optional

from vendor.interfaces.indicator import IndicatorInterface
from vendor.models.candle import CandleModel
from vendor.models.tick import TickModel
from vendor.services.logging import LoggingService

from .models.value import RSIBollingerBandsValueModel


class RSIBollingerBandsIndicator(IndicatorInterface):
    """Bollinger Bands applied to RSI values for overbought/oversold detection."""

    _NAME: str = "RSI Bollinger Bands"
    _MIN_CANDLES_REQUIRED: int = 2

    _key: str
    _rsi_period: int
    _bollinger_period: int
    _deviation: float
    _price_to_use: str
    _candles: List[CandleModel]
    _values: List[RSIBollingerBandsValueModel]
    _rsi_values: List[float]
    _gains: List[float]
    _losses: List[float]
    _avg_gain: float
    _avg_loss: float

    _log: LoggingService

    def __init__(
        self,
        key: str,
        rsi_period: int = 10,
        bollinger_period: int = 5,
        deviation: float = 1.7,
        price_to_use: str = "close_price",
        candles: Optional[List[CandleModel]] = None,
    ) -> None:
        """Initialize RSI Bollinger Bands indicator with configuration parameters."""
        self._key = key
        self._rsi_period = rsi_period
        self._bollinger_period = bollinger_period
        self._deviation = deviation
        self._price_to_use = price_to_use
        self._candles = candles if candles is not None else []
        self._values = []
        self._rsi_values = []
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
        """Recalculate RSI and Bollinger Bands values."""
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

        rsi_value = 0.0

        if len(self._gains) < self._rsi_period:
            rsi_value = 0.0
        elif len(self._gains) == self._rsi_period:
            self._avg_gain = sum(self._gains) / self._rsi_period
            self._avg_loss = sum(self._losses) / self._rsi_period

            if self._avg_loss == 0:
                rsi_value = 100.0
            else:
                relative_strength = self._avg_gain / self._avg_loss
                rsi_value = 100.0 - (100.0 / (1.0 + relative_strength))
        else:
            alpha = 1.0 / self._rsi_period
            self._avg_gain = (alpha * gain) + ((1 - alpha) * self._avg_gain)
            self._avg_loss = (alpha * loss) + ((1 - alpha) * self._avg_loss)

            if self._avg_loss == 0:
                rsi_value = 100.0
            else:
                relative_strength = self._avg_gain / self._avg_loss
                rsi_value = 100.0 - (100.0 / (1.0 + relative_strength))

        self._rsi_values.append(rsi_value)

        result = RSIBollingerBandsValueModel()
        result.date = current_candle.close_time
        result.rsi_value = rsi_value

        if len(self._rsi_values) >= self._bollinger_period:
            recent_rsi = self._rsi_values[-self._bollinger_period :]
            middle_band = sum(recent_rsi) / self._bollinger_period

            variance_sum = sum((rsi - middle_band) ** 2 for rsi in recent_rsi)
            standard_deviation = math.sqrt(variance_sum / (self._bollinger_period - 1))

            result.middle_band = middle_band
            result.upper_band = middle_band + (self._deviation * standard_deviation)
            result.lower_band = middle_band - (self._deviation * standard_deviation)

        self._values.append(result)

    def _should_refresh(self, candle_close_time: datetime.datetime) -> bool:
        if len(self._values) == 0:
            return True

        last_date = self._values[-1].date
        return last_date is None or last_date < candle_close_time

    @property
    def values(self) -> List[RSIBollingerBandsValueModel]:
        """Return the list of calculated RSI Bollinger Bands values."""
        return self._values

    @property
    def rsi_value(self) -> Optional[float]:
        """Return the current RSI value."""
        if len(self._values) == 0:
            return None
        return self._values[-1].rsi_value

    @property
    def upper_band(self) -> Optional[float]:
        """Return the current upper Bollinger Band value."""
        if len(self._values) == 0:
            return None
        return self._values[-1].upper_band

    @property
    def middle_band(self) -> Optional[float]:
        """Return the current middle Bollinger Band value."""
        if len(self._values) == 0:
            return None
        return self._values[-1].middle_band

    @property
    def lower_band(self) -> Optional[float]:
        """Return the current lower Bollinger Band value."""
        if len(self._values) == 0:
            return None
        return self._values[-1].lower_band
