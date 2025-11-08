import datetime
from typing import Any, Dict, List, Optional

from interfaces.indicator import IndicatorInterface
from models.tick import TickModel
from services.logging import LoggingService

from .models.value import VolatilityValueModel


class VolatilityIndicator(IndicatorInterface):
    _MIN_TICKS_REQUIRED: int = 2
    _INITIAL_VOLATILITY: float = 0.0

    _name: str = "Volatility"
    _key: str
    _window_size: int
    _candles: List[Dict[str, Any]]
    _price_to_use: str
    _values: List[VolatilityValueModel]
    _prices: List[float]
    _returns: List[float]

    def __init__(
        self,
        key: str,
        window_size: int = 20,
        price_to_use: str = "close_price",
        candles: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        self._key = key
        self._window_size = window_size
        self._price_to_use = price_to_use
        self._candles = candles if candles is not None else []
        self._values = []
        self._prices = []
        self._returns = []

        self._log = LoggingService()
        self._log.setup("volatility_indicator")

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
            value = VolatilityValueModel()
            value.date = self._candles[-1]["close_time"]
            value.value = self._INITIAL_VOLATILITY
            self._values.append(value)
            return

        price_return = (self._prices[-1] - self._prices[-2]) / self._prices[-2]
        self._returns.append(price_return)

        window_start = max(0, len(self._returns) - self._window_size)
        window_returns = self._returns[window_start:]

        value = VolatilityValueModel()
        value.date = self._candles[-1]["close_time"]
        value.value = self._compute_std(window_returns)

        self._values.append(value)

    def _compute_std(self, returns: List[float]) -> float:
        if len(returns) == 0:
            return 0.0

        mean = sum(returns) / len(returns)
        variance = sum((r - mean) ** 2 for r in returns) / len(returns)
        return variance**0.5

    def _should_refresh(self, candle_close_time: datetime.datetime) -> bool:
        if len(self._values) == 0:
            return True

        return self._values[-1].date < candle_close_time

    @property
    def values(self) -> List[VolatilityValueModel]:
        return self._values

