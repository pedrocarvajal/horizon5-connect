import datetime
from typing import Any, Dict, List, Optional

from interfaces.indicator import IndicatorInterface
from models.tick import TickModel
from services.logging import LoggingService

from .models.value import PriceAccelerationValueModel


class PriceAccelerationIndicator(IndicatorInterface):
    # ───────────────────────────────────────────────────────────
    # CONSTANTS
    # ───────────────────────────────────────────────────────────
    MIN_TICKS_REQUIRED: int = 3
    MIN_PRICES_FOR_VELOCITY: int = 2
    MIN_VELOCITIES_FOR_ACCELERATION: int = 2
    INITIAL_ACCELERATION: float = 0.0

    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    _name: str = "Price Acceleration"
    _key: str
    _window_size: int
    _candles: List[Dict[str, Any]]
    _price_to_use: str
    _values: List[PriceAccelerationValueModel]
    _prices: List[float]
    _velocities: List[float]
    _accelerations: List[float]

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
        self._accelerations = []

        self._log = LoggingService()
        self._log.setup("price_acceleration_indicator")

    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def on_tick(self, tick: TickModel) -> None:
        super().on_tick(tick)

        if len(self._candles) < self.MIN_TICKS_REQUIRED:
            return

        if (
            len(self._candles) > 0
            and tick.date >= self._candles[-1]["close_time"]
            and self._should_refresh(self._candles[-1]["close_time"])
        ):
            self.refresh()

    def refresh(self) -> None:
        if len(self._candles) < self.MIN_TICKS_REQUIRED:
            return

        current_price = self._candles[-1][self._price_to_use]
        self._prices.append(current_price)

        if len(self._prices) < self.MIN_PRICES_FOR_VELOCITY:
            value = PriceAccelerationValueModel()
            value.date = self._candles[-1]["close_time"]
            value.value = self.INITIAL_ACCELERATION
            self._values.append(value)
            return

        velocity = self._prices[-1] - self._prices[-2]
        self._velocities.append(velocity)

        if len(self._velocities) < self.MIN_VELOCITIES_FOR_ACCELERATION:
            value = PriceAccelerationValueModel()
            value.date = self._candles[-1]["close_time"]
            value.value = self.INITIAL_ACCELERATION
            self._values.append(value)
            return

        acceleration = self._velocities[-1] - self._velocities[-2]
        self._accelerations.append(acceleration)

        window_start = max(0, len(self._accelerations) - self._window_size)
        window_accelerations = self._accelerations[window_start:]

        value = PriceAccelerationValueModel()
        value.date = self._candles[-1]["close_time"]
        value.value = sum(window_accelerations) / len(window_accelerations)

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
    def values(self) -> List[PriceAccelerationValueModel]:
        return self._values
