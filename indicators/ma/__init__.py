"""Moving Average indicator implementation."""

import datetime
from typing import Any, Dict, List, Optional

from interfaces.indicator import IndicatorInterface
from models.tick import TickModel
from services.logging import LoggingService

from .models.value import MAValueModel


class MAIndicator(IndicatorInterface):
    """Simple and Exponential Moving Average indicator for price analysis."""

    _MULTIPLIER_COEFFICIENT: int = 2

    _name: str = "Moving Average"
    _key: str
    _period: int
    _price_to_use: str
    _exponential: bool
    _candles: List[Dict[str, Any]]
    _values: List[MAValueModel]

    def __init__(
        self,
        key: str,
        period: int = 5,
        price_to_use: str = "close_price",
        exponential: bool = False,
        candles: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Initialize the Moving Average indicator with configuration parameters."""
        self._key = key
        self._period = period
        self._price_to_use = price_to_use
        self._exponential = exponential
        self._candles = candles if candles is not None else []
        self._values = []

        self._log = LoggingService()
        self._log.setup("ma_indicator")

    def on_tick(self, tick: TickModel) -> None:
        """Process incoming tick and refresh indicator if candle closed."""
        super().on_tick(tick)

        if len(self._candles) < self._period:
            return

        if (
            len(self._candles) > 0
            and tick.date >= self._candles[-1]["close_time"]
            and self._should_refresh(self._candles[-1]["close_time"])
        ):
            self.refresh()

    def refresh(self) -> None:
        """Recalculate the moving average value based on current candles."""
        if len(self._candles) < self._period:
            return

        prices = [candle[self._price_to_use] for candle in self._candles[-self._period :]]

        if len(prices) < self._period:
            return

        value = MAValueModel()
        value.date = self._candles[-1]["close_time"]

        if self._exponential:
            if len(self._values) == 0:
                value.value = self._compute_exponential(prices)
            else:
                multiplier = self._MULTIPLIER_COEFFICIENT / (self._period + 1)
                current_price = self._candles[-1][self._price_to_use]
                value.value = (current_price * multiplier) + (self._values[-1].value * (1 - multiplier))
        else:
            value.value = self._compute_simple(prices)

        self._values.append(value)

    def _compute_exponential(self, prices: List[float]) -> float:
        multiplier = self._MULTIPLIER_COEFFICIENT / (self._period + 1)
        exponential_moving_average = prices[0]

        for price in prices[1:]:
            exponential_moving_average = (price * multiplier) + (exponential_moving_average * (1 - multiplier))

        return exponential_moving_average

    def _compute_simple(self, prices: List[float]) -> float:
        return sum(prices) / len(prices)

    def _should_refresh(self, candle_close_time: datetime.datetime) -> bool:
        if len(self._values) == 0:
            return True

        last_date = self._values[-1].date
        return last_date is None or last_date < candle_close_time
