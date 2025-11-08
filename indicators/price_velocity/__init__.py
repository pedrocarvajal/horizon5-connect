import datetime
from typing import Any, Dict, List, Optional

from interfaces.indicator import IndicatorInterface
from models.tick import TickModel
from services.logging import LoggingService

from .models.value import PriceVelocityValueModel


class PriceVelocityIndicator(IndicatorInterface):
    # ───────────────────────────────────────────────────────────
    # CONSTANTS
    # ───────────────────────────────────────────────────────────
    _MIN_TICKS_REQUIRED: int = 2
    _INITIAL_VELOCITY: float = 0.0

    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    _name: str = "Price Velocity"
    _key: str
    _window_size: int
    _candles: List[Dict[str, Any]]
    _price_to_use: str
    _values: List[PriceVelocityValueModel]
    _prices: List[float]
    _velocities: List[float]

    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(
        self,
        key: str,
        window_size: int = 5,
        price_to_use: str = "close_price",
        candles: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        self._key = key
        self._window_size = window_size
        self._price_to_use = price_to_use
        self._candles = candles if candles is not None else []
        self._values = []
        self._prices = []
        self._velocities = []

        self._log = LoggingService()
        self._log.setup("price_velocity_indicator")

    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def on_tick(self, tick: TickModel) -> None:
        super().on_tick(tick)

        if len(self._candles) < self._MIN_TICKS_REQUIRED:
            return

        if (
            len(self._candles) > 0
            and tick.date >= self._candles[-1]["close_time"]
            and self._should_refresh(self._candles[-1]["close_time"])
        ):
            self.refresh()

    def refresh(self) -> None:
        if len(self._candles) < self._MIN_TICKS_REQUIRED:
            return

        current_price = self._candles[-1][self._price_to_use]
        self._prices.append(current_price)

        if len(self._prices) < 2:
            value = PriceVelocityValueModel()
            value.date = self._candles[-1]["close_time"]
            value.value = self._INITIAL_VELOCITY
            self._values.append(value)
            return

        velocity = self._prices[-1] - self._prices[-2]
        self._velocities.append(velocity)

        window_start = max(0, len(self._velocities) - self._window_size)
        window_velocities = self._velocities[window_start:]

        value = PriceVelocityValueModel()
        value.date = self._candles[-1]["close_time"]
        value.value = sum(window_velocities) / len(window_velocities)

        self._values.append(value)

    # ───────────────────────────────────────────────────────────
    # PRIVATE METHODS
    # ───────────────────────────────────────────────────────────
    def _should_refresh(self, candle_close_time: datetime.datetime) -> bool:
        if len(self._values) == 0:
            return True

        return self._values[-1].date < candle_close_time

    # ───────────────────────────────────────────────────────────
    # GETTERS
    # ───────────────────────────────────────────────────────────
    @property
    def values(self) -> List[PriceVelocityValueModel]:
        return self._values
