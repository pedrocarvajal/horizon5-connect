"""EMA5 breakout trading strategy implementation."""

import datetime
from typing import Any, ClassVar, Dict, Optional

from enums.order_side import OrderSide
from enums.order_status import OrderStatus
from enums.quality_method import QualityMethod
from enums.timeframe import Timeframe
from indicators.ma import MAIndicator
from models.backtest_expectation import BacktestExpectationModel
from models.order import OrderModel
from models.tick import TickModel
from services.candle import CandleService
from services.strategy import StrategyService
from strategies.ema5_breakout.enums import OrderOpeningMode


class EMA5BreakoutStrategy(StrategyService):
    """Trading strategy based on EMA5 breakout with MA200 trend filter.

    Entry Rules:
    - EMA5 crosses above previous day's EMA5 maximum
    - Price above MA200 (trend filter)
    - Configurable order opening modes (ONE_AT_A_TIME, ONE_PER_DAY, ONE_PER_WEEK)
    - Only BUY orders (long-only strategy)

    Exit Rules:
    - Initial stop loss: percentage-based below entry
    - Trailing stop: activated after price reaches activation threshold
    - Trailing exit level: follows EMA5 upward, closes when price crosses below

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

    _SETTINGS: ClassVar[Dict[str, Any]] = {
        "order_opening_mode": OrderOpeningMode.ONE_AT_A_TIME,
        "volume_percentage": 0.10,
        "ema_period": 5,
        "ma_trend_period": 200,
        "stop_loss_percentage": 0.15,
        "trailing_activation_percentage": 0.03,
    }

    _enabled = False
    _name = "EMA5Breakout"
    _settings: Dict[str, Any]

    def __init__(self, **kwargs: Any) -> None:
        """Initialize EMA5 breakout strategy with configuration.

        Args:
            **kwargs: Keyword arguments including optional 'settings' dict with:
                - order_opening_mode: Order opening mode (default: ONE_AT_A_TIME)
                - volume_percentage: Order size as % of NAV (default: 0.10)
                - ema_period: EMA period for entry signal (default: 5)
                - ma_trend_period: MA period for trend filter (default: 200)
                - stop_loss_percentage: Stop loss as % below entry (default: 0.15)
                - trailing_activation_percentage: % gain to activate trailing (default: 0.03)
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

        ema_period = self._settings.get("ema_period", 5)
        ma_trend_period = self._settings.get("ma_trend_period", 200)

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
                    MAIndicator(
                        key="ma_trend",
                        period=ma_trend_period,
                        price_to_use="close_price",
                        is_exponential=False,
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
        """Handle new hour event by checking trailing exit and entry conditions."""
        super().on_new_hour()
        self._check_trailing_exit()
        self._check_entry_conditions()

    def on_new_day(self) -> None:
        """Handle new day event by calculating previous day's EMA5 maximum."""
        super().on_new_day()
        assert self._tick is not None
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
            profit_percentage = order.profit_percentage * 100
            profit = order.profit

            self._log.info(f"Order: {order.id}, was closed, with profit: {profit:.2f} ({profit_percentage:.2f}%).")

    def _can_open_new_order(self) -> bool:
        """Check if a new order can be opened based on configured mode.

        Returns:
            True if order can be opened according to mode constraints.
        """
        assert self._tick is not None
        order_opening_mode = self._settings.get("order_opening_mode", OrderOpeningMode.ONE_AT_A_TIME)

        if order_opening_mode == OrderOpeningMode.ONE_AT_A_TIME:
            return len(self.orderbook.where(side=OrderSide.BUY, status=OrderStatus.OPEN)) == 0

        if order_opening_mode == OrderOpeningMode.ONE_PER_DAY:
            today = self._tick.date.replace(hour=0, minute=0, second=0, microsecond=0)

            for order in self.orderbook.where(side=OrderSide.BUY):
                if order.created_at and order.created_at >= today:
                    return False

            return True

        if order_opening_mode == OrderOpeningMode.ONE_PER_WEEK:
            current_date = self._tick.date.replace(hour=0, minute=0, second=0, microsecond=0)
            days_since_monday = current_date.weekday()
            week_start = current_date - datetime.timedelta(days=days_since_monday)

            for order in self.orderbook.where(side=OrderSide.BUY):
                if order.created_at and order.created_at >= week_start:
                    return False

            return True

        return True

    def _check_trailing_exit(self) -> None:
        """Check and update trailing stop for open orders."""
        assert self._tick is not None

        open_orders = self.orderbook.where(side=OrderSide.BUY, status=OrderStatus.OPEN)
        if len(open_orders) == 0:
            return

        candle_service = self._candles[Timeframe.ONE_HOUR]
        assert isinstance(candle_service, CandleService)
        candles = candle_service.candles

        if len(candles) < self._MIN_CANDLES_REQUIRED:
            return

        if "ema" not in candles[-1].indicators:
            return

        current_price = self._tick.price
        current_ema = candles[-1].indicators["ema"]["value"]
        activation_percentage = self._settings.get("trailing_activation_percentage", 0.03)

        for order in open_orders:
            activation_price = order.price + (order.price * activation_percentage)
            trailing_active = order.variables.get("trailing_active", False)
            trailing_exit_level = order.variables.get("trailing_exit_level", 0.0)

            if not trailing_active and current_price >= activation_price:
                order.variables["trailing_active"] = True
                order.variables["trailing_exit_level"] = current_ema
                self._log.info(
                    f"Trailing activated: order={order.id}, price={current_price:.2f}, EMA={current_ema:.2f}"
                )
                continue

            if trailing_active:
                if current_ema > trailing_exit_level:
                    order.variables["trailing_exit_level"] = current_ema
                    self._log.info(f"Trailing updated: order={order.id}, EMA={current_ema:.2f}")
                elif current_price <= trailing_exit_level:
                    self._log.info(
                        f"Trailing exit: order={order.id}, price={current_price:.2f}, level={trailing_exit_level:.2f}"
                    )
                    self.orderbook.close(order)

    def _check_entry_conditions(self) -> None:
        """Check entry conditions and open order if all conditions are met."""
        assert self._tick is not None

        if not self._previous_day_ema5_max:
            return

        if not self._can_open_new_order():
            return

        current_price = self._tick.price
        candle_service = self._candles[Timeframe.ONE_HOUR]
        assert isinstance(candle_service, CandleService)
        candles = candle_service.candles
        current_ema = candles[-1].indicators["ema"]["value"]
        previous_ema = candles[-2].indicators["ema"]["value"]

        if "ma_trend" not in candles[-1].indicators:
            return

        current_ma_trend = candles[-1].indicators["ma_trend"]["value"]

        if current_price <= current_ma_trend:
            return

        if previous_ema < self._previous_day_ema5_max and current_ema > self._previous_day_ema5_max:
            stop_loss_percentage = self._settings.get("stop_loss_percentage", 0.15)
            stop_loss_price = current_price - (current_price * stop_loss_percentage)

            volume_percentage = self._settings.get("volume_percentage", 0.10)
            volume = (self.nav / current_price) * volume_percentage

            self.open_order(
                OrderSide.BUY,
                current_price,
                0.0,
                stop_loss_price,
                volume,
            )

    def _calculate_previous_day_ema5_max(self, tick: TickModel) -> None:
        """Calculate maximum EMA5 value from previous day.

        Args:
            tick: Current market tick for date reference.
        """
        today = tick.date.replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday = today - datetime.timedelta(days=1)
        candle_service = self._candles[Timeframe.ONE_HOUR]
        assert isinstance(candle_service, CandleService)
        candles = candle_service.candles
        emas = [
            candle.indicators["ema"]
            for candle in candles[-self._MIN_CANDLES_FOR_PREVIOUS_DAY :]
            if "ema" in candle.indicators
        ]

        if len(emas) < self._MIN_CANDLES_FOR_PREVIOUS_DAY:
            self._log.warning(f"Not enough EMA values ({len(emas)}) to calculate.")
            return

        self._previous_day_ema5_max = max(
            [ema.get("value") for ema in emas if ema.get("date") >= yesterday and ema.get("date") < today]
        )
