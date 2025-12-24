"""Average Directional Index (ADX) indicator implementation."""

import datetime
from typing import List, Optional

from vendor.interfaces.indicator import IndicatorInterface
from vendor.interfaces.logging import LoggingInterface
from vendor.models.candle import CandleModel
from vendor.models.tick import TickModel
from vendor.services.logging import LoggingService

from .models.value import ADXValueModel


class ADXIndicator(IndicatorInterface):
    """ADX indicator for measuring trend strength."""

    _NAME: str = "Average Directional Index"
    _MIN_CANDLES_REQUIRED: int = 2

    _key: str
    _period: int
    _candles: List[CandleModel]
    _values: List[ADXValueModel]
    _true_ranges: List[float]
    _plus_dm: List[float]
    _minus_dm: List[float]
    _smoothed_tr: float
    _smoothed_plus_dm: float
    _smoothed_minus_dm: float
    _dx_values: List[float]

    _log: LoggingInterface

    def __init__(
        self,
        key: str,
        period: int = 14,
        candles: Optional[List[CandleModel]] = None,
    ) -> None:
        """Initialize the ADX indicator with configuration parameters."""
        self._key = key
        self._period = period
        self._candles = candles if candles is not None else []
        self._values = []
        self._true_ranges = []
        self._plus_dm = []
        self._minus_dm = []
        self._smoothed_tr = 0.0
        self._smoothed_plus_dm = 0.0
        self._smoothed_minus_dm = 0.0
        self._dx_values = []

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
        """Recalculate the ADX value based on current candles."""
        if len(self._candles) < self._MIN_CANDLES_REQUIRED:
            return

        current_candle = self._candles[-1]
        previous_candle = self._candles[-2]

        true_range = self._calculate_true_range(current_candle, previous_candle)
        plus_dm, minus_dm = self._calculate_directional_movement(current_candle, previous_candle)

        self._true_ranges.append(true_range)
        self._plus_dm.append(plus_dm)
        self._minus_dm.append(minus_dm)

        if len(self._true_ranges) < self._period:
            adx_value = ADXValueModel()
            adx_value.date = current_candle.close_time
            adx_value.adx = 0.0
            adx_value.plus_di = 0.0
            adx_value.minus_di = 0.0
            self._values.append(adx_value)
            return

        if len(self._true_ranges) == self._period:
            self._smoothed_tr = sum(self._true_ranges[-self._period :])
            self._smoothed_plus_dm = sum(self._plus_dm[-self._period :])
            self._smoothed_minus_dm = sum(self._minus_dm[-self._period :])
        else:
            self._smoothed_tr = self._smoothed_tr - (self._smoothed_tr / self._period) + true_range
            self._smoothed_plus_dm = self._smoothed_plus_dm - (self._smoothed_plus_dm / self._period) + plus_dm
            self._smoothed_minus_dm = self._smoothed_minus_dm - (self._smoothed_minus_dm / self._period) + minus_dm

        plus_di = 0.0
        minus_di = 0.0

        if self._smoothed_tr > 0:
            plus_di = (self._smoothed_plus_dm / self._smoothed_tr) * 100
            minus_di = (self._smoothed_minus_dm / self._smoothed_tr) * 100

        dx = 0.0
        di_sum = plus_di + minus_di
        if di_sum > 0:
            dx = (abs(plus_di - minus_di) / di_sum) * 100

        self._dx_values.append(dx)

        adx = 0.0
        if len(self._dx_values) >= self._period:
            if len(self._dx_values) == self._period:
                adx = sum(self._dx_values[-self._period :]) / self._period
            else:
                previous_adx = self._values[-1].adx if self._values else 0.0
                adx = ((previous_adx * (self._period - 1)) + dx) / self._period

        adx_value = ADXValueModel()
        adx_value.date = current_candle.close_time
        adx_value.adx = adx
        adx_value.plus_di = plus_di
        adx_value.minus_di = minus_di

        self._values.append(adx_value)

    def _calculate_true_range(self, current: CandleModel, previous: CandleModel) -> float:
        high_low = current.high_price - current.low_price
        high_close = abs(current.high_price - previous.close_price)
        low_close = abs(current.low_price - previous.close_price)
        return max(high_low, high_close, low_close)

    def _calculate_directional_movement(self, current: CandleModel, previous: CandleModel) -> tuple[float, float]:
        up_move = current.high_price - previous.high_price
        down_move = previous.low_price - current.low_price

        plus_dm = 0.0
        minus_dm = 0.0

        if up_move > down_move and up_move > 0:
            plus_dm = up_move

        if down_move > up_move and down_move > 0:
            minus_dm = down_move

        return plus_dm, minus_dm

    def _should_refresh(self, candle_close_time: datetime.datetime) -> bool:
        if len(self._values) == 0:
            return True

        last_date = self._values[-1].date
        return last_date is None or last_date < candle_close_time

    @property
    def values(self) -> List[ADXValueModel]:
        """Return the list of calculated ADX values."""
        return self._values

    @property
    def adx(self) -> Optional[float]:
        """Return the current ADX value."""
        if len(self._values) == 0:
            return None
        return self._values[-1].adx

    @property
    def plus_di(self) -> Optional[float]:
        """Return the current +DI value."""
        if len(self._values) == 0:
            return None
        return self._values[-1].plus_di

    @property
    def minus_di(self) -> Optional[float]:
        """Return the current -DI value."""
        if len(self._values) == 0:
            return None
        return self._values[-1].minus_di
