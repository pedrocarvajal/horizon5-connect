"""Turtle Trading strategy implementation based on Richard Dennis system."""

from typing import Any, ClassVar, Dict, List, Optional

from vendor.enums.order_side import OrderSide
from vendor.enums.order_status import OrderStatus
from vendor.enums.quality_method import QualityMethod
from vendor.enums.timeframe import Timeframe
from vendor.indicators.atr import ATRIndicator
from vendor.indicators.donchian_channel import DonchianChannelIndicator
from vendor.models.backtest_expectation import BacktestExpectationModel
from vendor.models.order import OrderModel
from vendor.models.tick import TickModel
from vendor.services.candle import CandleService
from vendor.services.strategy import StrategyService


class TurtleTradingStrategy(StrategyService):
    """Trading strategy based on the original Turtle Trading system.

    Entry Rules:
    - LONG: Price breaks above Donchian upper band (entry period)
    - SHORT: Price breaks below Donchian lower band (entry period, if enabled)
    - Only one position direction at a time

    Exit Rules:
    - LONG exit: Price breaks below Donchian lower band (exit period)
    - SHORT exit: Price breaks above Donchian upper band (exit period)
    - Stop loss: 2 * ATR from entry price

    Pyramiding:
    - Add positions every 0.5 * ATR in favorable direction
    - Maximum 4 units per trend

    Attributes:
        _enabled: Strategy activation flag.
        _name: Strategy identifier.
        _settings: Configuration parameters.
        _candles: Candle services for the trading timeframe.
        _pyramid_units: Current number of pyramid units.
        _last_pyramid_price: Price of last pyramid addition.
        _entry_atr: ATR value at initial entry.
    """

    _MIN_CANDLES_REQUIRED: int = 2

    _SETTINGS: ClassVar[Dict[str, Any]] = {
        "volume_percentage": 0.10,
        "donchian_entry_period": 20,
        "donchian_exit_period": 10,
        "atr_period": 20,
        "stop_loss_atr_multiplier": 2.0,
        "pyramid_atr_multiplier": 0.5,
        "max_pyramid_units": 4,
        "allow_short": False,
    }

    _enabled = True
    _name = "TurtleTrading"
    _settings: Dict[str, Any]

    def __init__(self, **kwargs: Any) -> None:
        """Initialize Turtle Trading strategy with configuration.

        Args:
            **kwargs: Keyword arguments including optional 'settings' dict with:
                - volume_percentage: Order size as % of NAV per unit (default: 0.10)
                - donchian_entry_period: Donchian period for entry (default: 20)
                - donchian_exit_period: Donchian period for exit (default: 10)
                - atr_period: ATR period for volatility (default: 20)
                - stop_loss_atr_multiplier: ATR multiplier for stop loss (default: 2.0)
                - pyramid_atr_multiplier: ATR interval for pyramiding (default: 0.5)
                - max_pyramid_units: Maximum pyramid units (default: 4)
                - allow_short: Enable short positions (default: False)
        """
        super().__init__(**kwargs)

        self._backtest_quality_method = QualityMethod.FQS
        self._backtest_expectation = BacktestExpectationModel(
            max_drawdown=[-0.30, 0],
            performance_percentage=[0.07, 1],
            r_squared=[0, 1],
        )

        settings = kwargs.get("settings", {})
        self._settings = {**self._SETTINGS, **settings}

        self._pyramid_units: int = 0
        self._last_pyramid_price: float = 0.0
        self._entry_atr: float = 0.0
        self._current_direction: Optional[OrderSide] = None
        self._previous_donchian_upper: Optional[float] = None
        self._previous_donchian_lower: Optional[float] = None

        donchian_entry_period = self._settings.get("donchian_entry_period", 20)
        donchian_exit_period = self._settings.get("donchian_exit_period", 10)
        atr_period = self._settings.get("atr_period", 20)

        self._candles = {
            Timeframe.FOUR_HOURS: CandleService(
                timeframe=Timeframe.FOUR_HOURS,
                indicators=[
                    DonchianChannelIndicator(
                        key="donchian_entry",
                        period=donchian_entry_period,
                    ),
                    DonchianChannelIndicator(
                        key="donchian_exit",
                        period=donchian_exit_period,
                    ),
                    ATRIndicator(
                        key="atr",
                        period=atr_period,
                    ),
                ],
            )
        }

    def on_tick(self, tick: TickModel) -> None:
        """Process incoming tick and update current tick reference.

        Args:
            tick: Current market tick data.
        """
        super().on_tick(tick)
        self._tick = tick

    def on_new_hour(self) -> None:
        """Handle new hour event - check signals on 4H candle close."""
        super().on_new_hour()

        candle_service = self._candles.get(Timeframe.FOUR_HOURS)
        if not isinstance(candle_service, CandleService):
            return

        if len(candle_service.candles) < self._MIN_CANDLES_REQUIRED:
            return

        current_candle = candle_service.candles[-1]
        previous_candle = candle_service.candles[-2]

        if current_candle.close_time == previous_candle.close_time:
            return

        self._check_exit_conditions()
        self._check_pyramid_conditions()
        self._check_entry_conditions()

        self._update_previous_donchian_levels()

    def on_transaction(self, order: OrderModel) -> None:
        """Handle order transaction events.

        Args:
            order: Order that triggered the transaction event.
        """
        super().on_transaction(order)

        if order.status.is_open():
            self._log.info(
                "Order opened",
                order_id=order.id,
                price=f"{order.price:.2f}",
                units=self._pyramid_units,
            )

        if order.status.is_closed():
            profit_percentage = order.profit_percentage * 100

            self._log.info(
                "Order closed",
                order_id=order.id,
                profit=f"{order.profit:.2f}",
                profit_percentage=f"{profit_percentage:.2f}%",
            )

            open_orders = self._get_open_orders()
            if len(open_orders) == 0:
                self._reset_pyramid_state()

    def _get_open_orders(self, side: Optional[OrderSide] = None) -> List[OrderModel]:
        if side:
            return self.orderbook.where(side=side, status=OrderStatus.OPEN)
        return self.orderbook.where(status=OrderStatus.OPEN)

    def _reset_pyramid_state(self) -> None:
        self._pyramid_units = 0
        self._last_pyramid_price = 0.0
        self._entry_atr = 0.0
        self._current_direction = None

    def _update_previous_donchian_levels(self) -> None:
        candle_service = self._candles.get(Timeframe.FOUR_HOURS)
        if not isinstance(candle_service, CandleService):
            return

        candles = candle_service.candles
        if len(candles) < self._MIN_CANDLES_REQUIRED:
            return

        closed_candle = candles[-2]
        if "donchian_entry" not in closed_candle.indicators:
            return

        self._previous_donchian_upper = closed_candle.indicators["donchian_entry"]["upper"]
        self._previous_donchian_lower = closed_candle.indicators["donchian_entry"]["lower"]

    def _check_entry_conditions(self) -> None:
        if not self._tick:
            return

        open_orders = self._get_open_orders()
        if len(open_orders) > 0:
            return

        candle_service = self._candles.get(Timeframe.FOUR_HOURS)
        if not isinstance(candle_service, CandleService):
            return

        candles = candle_service.candles
        if len(candles) < self._MIN_CANDLES_REQUIRED:
            return

        closed_candle = candles[-2]

        if "donchian_entry" not in closed_candle.indicators:
            return
        if "atr" not in closed_candle.indicators:
            return

        if not self._previous_donchian_upper or not self._previous_donchian_lower:
            return

        current_high = closed_candle.high_price
        current_low = closed_candle.low_price
        current_atr = closed_candle.indicators["atr"]["value"]
        allow_short = self._settings.get("allow_short", False)

        is_long_breakout = current_high > self._previous_donchian_upper
        is_short_breakout = current_low < self._previous_donchian_lower and allow_short

        if is_long_breakout:
            self._open_position(OrderSide.BUY, current_atr)
        elif is_short_breakout:
            self._open_position(OrderSide.SELL, current_atr)

    def _check_exit_conditions(self) -> None:
        if not self._tick:
            return

        open_orders = self._get_open_orders()
        if len(open_orders) == 0:
            return

        candle_service = self._candles.get(Timeframe.FOUR_HOURS)
        if not isinstance(candle_service, CandleService):
            return

        candles = candle_service.candles
        if len(candles) < self._MIN_CANDLES_REQUIRED:
            return

        closed_candle = candles[-2]

        if "donchian_exit" not in closed_candle.indicators:
            return

        donchian_exit_lower = closed_candle.indicators["donchian_exit"]["lower"]
        donchian_exit_upper = closed_candle.indicators["donchian_exit"]["upper"]
        current_low = closed_candle.low_price
        current_high = closed_candle.high_price

        for order in open_orders:
            should_exit = False

            if order.side == OrderSide.BUY and current_low < donchian_exit_lower:
                should_exit = True
                self._log.info(
                    "Donchian exit triggered (LONG)",
                    low=f"{current_low:.2f}",
                    exit_level=f"{donchian_exit_lower:.2f}",
                )

            elif order.side == OrderSide.SELL and current_high > donchian_exit_upper:
                should_exit = True
                self._log.info(
                    "Donchian exit triggered (SHORT)",
                    high=f"{current_high:.2f}",
                    exit_level=f"{donchian_exit_upper:.2f}",
                )

            if should_exit:
                self.orderbook.close(order)

    def _check_pyramid_conditions(self) -> None:
        if not self._tick:
            return

        if self._entry_atr <= 0:
            return

        max_units = self._settings.get("max_pyramid_units", 4)
        if self._pyramid_units >= max_units:
            return

        open_orders = self._get_open_orders()
        if len(open_orders) == 0:
            return

        candle_service = self._candles.get(Timeframe.FOUR_HOURS)
        if not isinstance(candle_service, CandleService):
            return

        candles = candle_service.candles
        if len(candles) < self._MIN_CANDLES_REQUIRED:
            return

        closed_candle = candles[-2]
        current_price = closed_candle.close_price

        pyramid_multiplier = self._settings.get("pyramid_atr_multiplier", 0.5)
        pyramid_interval = self._entry_atr * pyramid_multiplier

        if self._current_direction == OrderSide.BUY:
            price_move = current_price - self._last_pyramid_price
            if price_move >= pyramid_interval:
                self._add_pyramid_unit(OrderSide.BUY)

        elif self._current_direction == OrderSide.SELL:
            price_move = self._last_pyramid_price - current_price
            if price_move >= pyramid_interval:
                self._add_pyramid_unit(OrderSide.SELL)

    def _open_position(self, side: OrderSide, atr: float) -> None:
        if not self._tick:
            return

        current_price = self._tick.close_price
        stop_loss_multiplier = self._settings.get("stop_loss_atr_multiplier", 2.0)
        volume_percentage = self._settings.get("volume_percentage", 0.10)

        if side == OrderSide.BUY:
            stop_loss_price = current_price - (stop_loss_multiplier * atr)
        else:
            stop_loss_price = current_price + (stop_loss_multiplier * atr)

        volume = (self.nav / current_price) * volume_percentage

        self._entry_atr = atr
        self._pyramid_units = 1
        self._last_pyramid_price = current_price
        self._current_direction = side

        self.open_order(
            side,
            current_price,
            0.0,
            stop_loss_price,
            volume,
            variables={
                "unit": 1,
                "entry_atr": atr,
            },
        )

        self._log.info(
            "Opened position",
            side=side.name,
            price=f"{current_price:.2f}",
            stop_loss=f"{stop_loss_price:.2f}",
            atr=f"{atr:.2f}",
            volume=f"{volume:.6f}",
        )

    def _add_pyramid_unit(self, side: OrderSide) -> None:
        if not self._tick:
            return

        current_price = self._tick.close_price
        stop_loss_multiplier = self._settings.get("stop_loss_atr_multiplier", 2.0)
        volume_percentage = self._settings.get("volume_percentage", 0.10)

        if side == OrderSide.BUY:
            stop_loss_price = current_price - (stop_loss_multiplier * self._entry_atr)
        else:
            stop_loss_price = current_price + (stop_loss_multiplier * self._entry_atr)

        volume = (self.nav / current_price) * volume_percentage

        self._pyramid_units += 1
        self._last_pyramid_price = current_price

        self.open_order(
            side,
            current_price,
            0.0,
            stop_loss_price,
            volume,
            variables={
                "unit": self._pyramid_units,
                "entry_atr": self._entry_atr,
            },
        )

        self._log.info(
            "Added pyramid unit",
            side=side.name,
            unit=self._pyramid_units,
            price=f"{current_price:.2f}",
            stop_loss=f"{stop_loss_price:.2f}",
            volume=f"{volume:.6f}",
        )

        self._update_all_stop_losses(side, stop_loss_price)

    def _update_all_stop_losses(self, side: OrderSide, new_stop_loss: float) -> None:
        open_orders = self._get_open_orders(side)

        for order in open_orders:
            if order.stop_loss_price != new_stop_loss:
                order.stop_loss_price = new_stop_loss
