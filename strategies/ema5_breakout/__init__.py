"""EMA5 breakout trading strategy implementation."""

import datetime
from time import sleep
from typing import Any, ClassVar, Dict, Optional

from vendor.enums.order_side import OrderSide
from vendor.enums.order_status import OrderStatus
from vendor.enums.quality_method import QualityMethod
from vendor.enums.timeframe import Timeframe
from vendor.enums.tp_sl_method import TpSlMethod
from vendor.indicators.ma import MAIndicator
from vendor.models.backtest_expectation import BacktestExpectationModel
from vendor.models.order import OrderModel
from vendor.models.tick import TickModel
from vendor.services.candle import CandleService
from vendor.services.strategy import StrategyService, calculate_stop_loss, calculate_take_profit


class EMA5BreakoutStrategy(StrategyService):
    """Trading strategy based on EMA5 breakout.

    Entry Rules:
    - EMA5 crosses above previous day's EMA5 maximum
    - Minimum waiting time between orders (configurable in minutes)
    - Only BUY orders (long-only strategy)

    Exit Rules:
    - Take profit and stop loss based on configurable methods (PERCENTAGE, ATR, FIXED)

    Attributes:
        _enabled: Strategy activation flag.
        _name: Strategy identifier.
        _settings: Configuration parameters.
        _backtest_expectation: Expected thresholds for quality calculation.
        _candles: Candle services for the trading timeframe.
        _previous_day_ema5_max: Maximum EMA5 value from previous day.
    """

    _MIN_CANDLES_REQUIRED: int = 2
    _MIN_CANDLES_FOR_PREVIOUS_DAY: int = 24
    _WEEKDAY_MONDAY: int = 0
    _WEEKDAY_FRIDAY: int = 4
    _WEEKDAY_SATURDAY: int = 5
    _WEEKDAY_SUNDAY: int = 6

    _SETTINGS: ClassVar[Dict[str, Any]] = {
        "entry_allow_multiple": False,
        "entry_waiting_time": 0,
        "entry_volume": 0.1,
        "entry_ema_period": 5,
        "main_stop_loss": 0.15,
        "main_stop_loss_method": TpSlMethod.PERCENTAGE,
        "main_take_profit": 0.30,
        "main_take_profit_method": TpSlMethod.PERCENTAGE,
        "recovery_enabled": False,
        "recovery_maximum_layers": 10,
        "recovery_stop_loss": 0.15,
        "recovery_stop_loss_method": TpSlMethod.PERCENTAGE,
        "recovery_take_profit": 0.03,
        "recovery_take_profit_method": TpSlMethod.PERCENTAGE,
    }

    _enabled = False
    _name = "EMA5Breakout"
    _settings: Dict[str, Any]

    def __init__(self, **kwargs: Any) -> None:
        """Initialize EMA5 breakout strategy with configuration.

        Args:
            **kwargs: Keyword arguments including optional 'settings' dict with:
                - entry_allow_multiple: Allow multiple concurrent orders (default: False)
                - entry_waiting_time: Minimum minutes between orders (default: 0)
                - entry_volume: Order size in lots (default: 0.1, where 1 lot = 100 units)
                - entry_ema_period: EMA period for entry signal (default: 5)
                - main_stop_loss: Stop loss value (default: 0.15)
                - main_stop_loss_method: TpSlMethod for stop loss (default: PERCENTAGE)
                - main_take_profit: Take profit value (default: 0.30)
                - main_take_profit_method: TpSlMethod for take profit (default: PERCENTAGE)
                - recovery_enabled: Enable recovery layers on losing trades (default: False)
                - recovery_maximum_layers: Max recovery attempts (default: 10)
                - recovery_stop_loss: Recovery stop loss value (default: 0.15)
                - recovery_stop_loss_method: TpSlMethod for recovery SL (default: PERCENTAGE)
                - recovery_take_profit: Recovery take profit value (default: 0.03)
                - recovery_take_profit_method: TpSlMethod for recovery TP (default: PERCENTAGE)
        """
        super().__init__(**kwargs)

        self._backtest_quality_method = QualityMethod.FQS
        self._backtest_expectation = BacktestExpectationModel(
            num_trades=[5, 30],
            max_drawdown=[-0.25, -0.10],
            performance_percentage=[0.10, 0.50],
            profit_factor=[1.2, 2.5],
        )

        settings = kwargs.get("settings", {})
        self._settings = {**self._SETTINGS, **settings}
        self._previous_day_ema5_max: Optional[float] = None

        ema_period = self._settings.get("entry_ema_period", 5)

        self._candles = {
            Timeframe.ONE_HOUR: CandleService(
                timeframe=Timeframe.ONE_HOUR,
                indicators=[
                    MAIndicator(
                        key="ema",
                        period=ema_period,
                        price_to_use="close_price",
                        is_exponential=True,
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
        """Handle new hour event by checking entry conditions."""
        super().on_new_hour()
        self._check_entry_conditions()

        if self._tick is None:
            return

        candle_service = self._candles[Timeframe.ONE_HOUR]
        last_candle = candle_service.candles[-1]
        self._log.debug(f"New hour processed: {last_candle}")

    def on_new_day(self) -> None:
        """Handle new day event by calculating previous day's EMA5 maximum."""
        super().on_new_day()

        if self._tick is None:
            return

        self._calculate_previous_day_ema5_max(self._tick)

    def on_transaction(self, order: OrderModel) -> None:
        """Handle order transaction events and log status changes.

        Args:
            order: Order that triggered the transaction event.
        """
        super().on_transaction(order)

        if order.status.is_open():
            self._log.info(f"Order: {order.id}, was opened.")

        if order.status.is_closed():
            recovery_enabled = self._settings.get("recovery_enabled", False)
            profit_percentage = order.profit_percentage * 100
            profit = order.profit

            self._log.info(f"Order: {order.id}, was closed, with profit: {profit:.2f} ({profit_percentage:.2f}%).")

            if recovery_enabled and profit < 0:
                self._open_recovery_order(closed_order=order)

    def _can_open_new_order(self) -> bool:
        if self._tick is None:
            return False

        allow_multiple = self._settings.get("entry_allow_multiple", False)
        waiting_time = self._settings.get("entry_waiting_time", 0)
        open_orders = self.orderbook.where(side=OrderSide.BUY, status=OrderStatus.OPEN)
        orders = self.orderbook.where(side=OrderSide.BUY)
        created_at_dates = [order.created_at for order in orders if order.created_at is not None]

        if not allow_multiple and len(open_orders) > 0:
            return False

        if not orders:
            return True

        if not created_at_dates:
            return True

        last_created_at = max(created_at_dates)
        time_since_last_order = self._tick.date - last_created_at
        minimum_waiting_time = datetime.timedelta(minutes=waiting_time)

        return time_since_last_order >= minimum_waiting_time

    def _check_entry_conditions(self) -> None:
        if self._tick is None:
            return

        if not self._previous_day_ema5_max:
            return

        if not self._can_open_new_order():
            return

        current_price = self._tick.price
        candle_service = self._candles[Timeframe.ONE_HOUR]
        candles = candle_service.candles
        current_ema = candles[-1].indicators["ema"]["value"]
        previous_ema = candles[-2].indicators["ema"]["value"]

        if previous_ema < self._previous_day_ema5_max and current_ema > self._previous_day_ema5_max:
            stop_loss_value = self._settings.get("main_stop_loss", 0.15)
            stop_loss_method = self._settings.get("main_stop_loss_method", TpSlMethod.PERCENTAGE)
            take_profit_value = self._settings.get("main_take_profit", 0.30)
            take_profit_method = self._settings.get("main_take_profit_method", TpSlMethod.PERCENTAGE)

            stop_loss_price = calculate_stop_loss(
                entry_price=current_price,
                value=stop_loss_value,
                method=stop_loss_method,
                side=OrderSide.BUY,
            )

            take_profit_price = calculate_take_profit(
                entry_price=current_price,
                value=take_profit_value,
                method=take_profit_method,
                side=OrderSide.BUY,
            )

            entry_volume = self._settings.get("entry_volume", 0.1)
            volume = entry_volume * 100

            self._log.info(
                f"Opening main order: price={current_price:.5f}, "
                + f"date={self._tick.date}, "
                + f"current_ema={current_ema}, "
                + f"previous_day_ema5_max={self._previous_day_ema5_max}, "
                + f"tp={take_profit_price:.5f} ({take_profit_method.name}:{take_profit_value}), "
                + f"sl={stop_loss_price:.5f} ({stop_loss_method.name}:{stop_loss_value}), "
                + f"volume={volume:.2f}"
            )

            self.open_order(
                OrderSide.BUY,
                current_price,
                take_profit_price,
                stop_loss_price,
                volume,
                variables={"layer": 0},
            )

    def _open_recovery_order(self, closed_order: OrderModel) -> None:
        if self._tick is None:
            return

        maximum_layers = self._settings.get("recovery_maximum_layers", 10)
        current_layer = closed_order.variables.get("layer", 0)
        next_layer = current_layer + 1

        if next_layer > maximum_layers:
            self._log.warning(f"Maximum recovery layers reached: {maximum_layers}")
            sleep(10)
            return

        current_price = self._tick.price
        losses = abs(closed_order.profit)

        stop_loss_value = self._settings.get("recovery_stop_loss", 0.15)
        stop_loss_method = self._settings.get("recovery_stop_loss_method", TpSlMethod.PERCENTAGE)
        take_profit_value = self._settings.get("recovery_take_profit", 0.03)
        take_profit_method = self._settings.get("recovery_take_profit_method", TpSlMethod.PERCENTAGE)

        stop_loss_price = calculate_stop_loss(
            entry_price=current_price,
            value=stop_loss_value,
            method=stop_loss_method,
            side=OrderSide.BUY,
        )

        take_profit_price = calculate_take_profit(
            entry_price=current_price,
            value=take_profit_value,
            method=take_profit_method,
            side=OrderSide.BUY,
        )

        volume = self._calculate_volume_for_recovery(
            losses=losses,
            entry_price=current_price,
            take_profit_price=take_profit_price,
        )

        self._log.info(f"Opening recovery layer {next_layer}: losses={losses:.2f}, volume={volume:.6f}")

        self.open_order(
            OrderSide.BUY,
            current_price,
            take_profit_price,
            stop_loss_price,
            volume,
            variables={"layer": next_layer},
        )

    def _calculate_volume_for_recovery(
        self,
        losses: float,
        entry_price: float,
        take_profit_price: float,
    ) -> float:
        if take_profit_price <= entry_price:
            return 0.0

        return losses / (take_profit_price - entry_price)

    def _calculate_previous_day_ema5_max(self, tick: TickModel) -> None:
        today_start = tick.date.replace(hour=0, minute=0, second=0, microsecond=0)
        weekday = today_start.weekday()

        if weekday == self._WEEKDAY_MONDAY:
            days_back = 3
        elif weekday == self._WEEKDAY_SUNDAY:
            days_back = 2
        elif weekday == self._WEEKDAY_SATURDAY:
            days_back = 1
        else:
            days_back = 1

        previous_trading_day_start = today_start - datetime.timedelta(days=days_back)
        previous_trading_day_end = previous_trading_day_start + datetime.timedelta(days=1)

        candle_service = self._candles[Timeframe.ONE_HOUR]
        candles = candle_service.candles
        recent_candles = candles[-72:]

        previous_day_ema_values = [
            candle.indicators["ema"]["value"]
            for candle in recent_candles
            if "ema" in candle.indicators
            and candle.open_time >= previous_trading_day_start
            and candle.open_time < previous_trading_day_end
        ]

        if not previous_day_ema_values:
            return

        self._previous_day_ema5_max = max(previous_day_ema_values)
