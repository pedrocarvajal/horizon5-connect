import datetime
from typing import Any, Dict, List, Optional

from interfaces.indicator import IndicatorInterface
from models.tick import TickModel
from services.logging import LoggingService

from .models.value import MAValueModel


class MAIndicator(IndicatorInterface):
    # ───────────────────────────────────────────────────────────
    # CONSTANTS
    # ───────────────────────────────────────────────────────────
    _MULTIPLIER_COEFFICIENT: int = 2

    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    _name: str = "Moving Average"
    _period: int
    _price_to_use: str
    _exponential: bool
    _candles: List[Dict[str, Any]]
    _values: List[MAValueModel]

    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(
        self,
        period: int = 5,
        price_to_use: str = "close_price",
        exponential: bool = False,
        candles: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        self._period = period
        self._price_to_use = price_to_use
        self._exponential = exponential
        self._candles = candles if candles is not None else []
        self._values = []

        self._log = LoggingService()
        self._log.setup("ma_indicator")

    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def on_tick(self, tick: TickModel) -> None:
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
        if len(self._candles) < self._period:
            return

        prices = [
            candle[self._price_to_use] for candle in self._candles[-self._period :]
        ]

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
                value.value = (current_price * multiplier) + (
                    self._values[-1].value * (1 - multiplier)
                )
        else:
            value.value = self._compute_simple(prices)

        self._values.append(value)

    # ───────────────────────────────────────────────────────────
    # PRIVATE METHODS
    # ───────────────────────────────────────────────────────────
    def _compute_exponential(self, prices: List[float]) -> float:
        multiplier = self._MULTIPLIER_COEFFICIENT / (self._period + 1)
        exponential_moving_average = prices[0]

        for price in prices[1:]:
            exponential_moving_average = (price * multiplier) + (
                exponential_moving_average * (1 - multiplier)
            )

        return exponential_moving_average

    def _compute_simple(self, prices: List[float]) -> float:
        return sum(prices) / len(prices)

    def _should_refresh(self, candle_close_time: datetime.datetime) -> bool:
        if len(self._values) == 0:
            return True

        return self._values[-1].date < candle_close_time

    # ───────────────────────────────────────────────────────────
    # GETTERS
    # ───────────────────────────────────────────────────────────
    @property
    def values(self) -> List[MAValueModel]:
        return self._values
