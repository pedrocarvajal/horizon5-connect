"""Donchian Channel breakout trading strategy implementation."""

from typing import Any, Dict

from vendor.enums.order_side import OrderSide
from vendor.enums.order_status import OrderStatus
from vendor.enums.quality_method import QualityMethod
from vendor.enums.timeframe import Timeframe
from vendor.indicators.adx import ADXIndicator
from vendor.indicators.atr import ATRIndicator
from vendor.indicators.donchian_channel import DonchianChannelIndicator
from vendor.indicators.ma import MAIndicator
from vendor.models.backtest_expectation import BacktestExpectationModel
from vendor.models.order import OrderModel
from vendor.models.tick import TickModel
from vendor.services.candle import CandleService
from vendor.services.strategy import StrategyService


class DonchianBreakoutStrategy(StrategyService):
    """Trading strategy based on Donchian Channel breakout with trend filters.

    Entry Rules:
    - Price closes above SMA (trend filter)
    - High breaks above Donchian upper band (breakout)
    - ADX above threshold (trend strength confirmation)
    - Bullish candle (close > open)
    - Only BUY orders (long-only strategy)

    Exit Rules:
    - Take profit: ATR multiplier above entry
    - Stop loss: ATR multiplier below entry
    - Optional trailing stop using Donchian lower band after TP activation

    Attributes:
        _enabled: Strategy activation flag.
        _name: Strategy identifier.
        _settings: Configuration parameters.
        _backtest_expectation: Expected thresholds for quality calculation.
        _candles: Candle services for the trading timeframe.
        _trailing_active: Whether trailing stop is currently active.
        _trailing_exit_level: Current trailing exit price level.
        _atr_at_entry: ATR value captured at order entry.
    """

    _MIN_CANDLES_FOR_ATR: int = 1
    _MIN_CANDLES_REQUIRED: int = 2

    _enabled = False
    _name = "DonchianBreakout"
    _settings: Dict[str, Any]

    def __init__(self, **kwargs: Any) -> None:
        """Initialize Donchian breakout strategy with configuration.

        Args:
            **kwargs: Keyword arguments including optional 'settings' dict with:
                - volume_percentage: Order size as % of NAV (default: 0.05)
                - sma_period: SMA period for trend filter (default: 200)
                - donchian_entry_period: Donchian period for entry (default: 20)
                - donchian_exit_period: Donchian period for trailing exit (default: 20)
                - adx_period: ADX period (default: 25)
                - atr_period: ATR period (default: 16)
                - adx_threshold: Minimum ADX for trend strength (default: 15.0)
                - take_profit_atr_multiplier: ATR multiplier for TP (default: 2.5)
                - stop_loss_atr_multiplier: ATR multiplier for SL (default: 1.5)
                - trailing_enabled: Enable Donchian trailing stop (default: True)
                - dynamic_atr: Use current ATR vs entry ATR (default: False)
        """
        super().__init__(**kwargs)

        self._backtest_quality_method = QualityMethod.FQS
        self._backtest_expectation = BacktestExpectationModel(
            num_trades=[12, 12 * 28],
            max_drawdown=[-0.30, 0],
            performance_percentage=[0.12, 0.50],
            profit_factor=[1, 3.0],
            r_squared=[0.7, 1],
        )

        self._settings = kwargs.get(
            "settings",
            {
                "volume_percentage": 1.0,
                "sma_period": 200,
                "donchian_entry_period": 20,
                "donchian_exit_period": 20,
                "adx_period": 25,
                "atr_period": 16,
                "adx_threshold": 15.0,
                "take_profit_atr_multiplier": 2.5,
                "stop_loss_atr_multiplier": 1.5,
                "trailing_enabled": True,
                "dynamic_atr": False,
            },
        )

        self._trailing_active: bool = False
        self._trailing_exit_level: float = 0.0
        self._atr_at_entry: float = 0.0

        sma_period = self._settings.get("sma_period", 200)
        donchian_entry_period = self._settings.get("donchian_entry_period", 20)
        donchian_exit_period = self._settings.get("donchian_exit_period", 20)
        adx_period = self._settings.get("adx_period", 25)
        atr_period = self._settings.get("atr_period", 16)

        self._candles = {
            Timeframe.FOUR_HOURS: CandleService(
                timeframe=Timeframe.FOUR_HOURS,
                indicators=[
                    MAIndicator(
                        key="sma",
                        period=sma_period,
                        price_to_use="close_price",
                        is_exponential=False,
                    ),
                    DonchianChannelIndicator(
                        key="donchian_entry",
                        period=donchian_entry_period,
                    ),
                    DonchianChannelIndicator(
                        key="donchian_exit",
                        period=donchian_exit_period,
                    ),
                    ADXIndicator(
                        key="adx",
                        period=adx_period,
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
        """Handle new hour event - check trailing and entry on 4H candle close."""
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

        self._check_trailing_exit()
        self._check_entry_conditions()

    def on_transaction(self, order: OrderModel) -> None:
        """Handle order transaction events and log status changes.

        Args:
            order: Order that triggered the transaction event.
        """
        super().on_transaction(order)

        if order.status.is_open():
            self._log.info(
                "Order opened",
                order_id=order.id,
                price=f"{order.price:.2f}",
            )

        if order.status.is_closed():
            profit_percentage = order.profit_percentage * 100
            profit = order.profit

            self._log.info(
                "Order closed",
                order_id=order.id,
                profit=f"{profit:.2f}",
                profit_percentage=f"{profit_percentage:.2f}%",
            )

            self._trailing_active = False
            self._trailing_exit_level = 0.0
            self._atr_at_entry = 0.0

    def _check_entry_conditions(self) -> None:
        candle_service = self._candles.get(Timeframe.FOUR_HOURS)

        if not isinstance(candle_service, CandleService):
            return

        candles = candle_service.candles
        if len(candles) < self._MIN_CANDLES_REQUIRED:
            return

        closed_candle = candles[-2]

        if "sma" not in closed_candle.indicators:
            return
        if "donchian_entry" not in closed_candle.indicators:
            return
        if "adx" not in closed_candle.indicators:
            return
        if "atr" not in closed_candle.indicators:
            return

        if len(self.orderbook.where(side=OrderSide.BUY, status=OrderStatus.OPEN)) > 0:
            return

        current_close = closed_candle.close_price
        current_high = closed_candle.high_price
        current_open = closed_candle.open_price
        current_sma = closed_candle.indicators["sma"]["value"]
        donchian_upper = closed_candle.indicators["donchian_entry"]["upper"]
        current_adx = closed_candle.indicators["adx"]["adx"]
        current_atr = closed_candle.indicators["atr"]["value"]

        adx_threshold = self._settings.get("adx_threshold", 15.0)

        condition_trend = current_close > current_sma
        condition_breakout = current_high >= donchian_upper
        condition_strength = current_adx > adx_threshold
        condition_bullish = current_close > current_open

        if condition_trend and condition_breakout and condition_strength and condition_bullish:
            message = (
                f"BREAKOUT SIGNAL: close={current_close:.2f} > sma={current_sma:.2f}, "
                f"high={current_high:.2f} >= donchian={donchian_upper:.2f}, "
                f"adx={current_adx:.2f} > {adx_threshold}"
            )
            self._log.info(message)
            self._open_long_order(current_atr)

    def _check_trailing_exit(self) -> None:
        if self._tick is None:
            return

        trailing_enabled = self._settings.get("trailing_enabled", True)
        if not trailing_enabled:
            return

        open_orders = self.orderbook.where(side=OrderSide.BUY, status=OrderStatus.OPEN)
        if len(open_orders) == 0:
            return

        order = open_orders[0]
        current_bid = self._tick.close_price

        dynamic_atr = self._settings.get("dynamic_atr", False)
        atr_value = self._get_current_atr() if dynamic_atr else self._atr_at_entry

        if atr_value <= 0:
            return

        tp_multiplier = self._settings.get("take_profit_atr_multiplier", 2.5)
        take_profit_activation = order.price + (tp_multiplier * atr_value)

        if not self._trailing_active and current_bid >= take_profit_activation:
            self._trailing_active = True
            self._log.info(
                "Trailing activated",
                bid=f"{current_bid:.2f}",
                activation=f"{take_profit_activation:.2f}",
            )

        if self._trailing_active:
            candle_service = self._candles.get(Timeframe.FOUR_HOURS)
            if not isinstance(candle_service, CandleService):
                return

            candles = candle_service.candles
            if len(candles) < self._MIN_CANDLES_REQUIRED:
                return

            previous_candle = candles[-2]
            if "donchian_exit" not in previous_candle.indicators:
                return

            donchian_lower = previous_candle.indicators["donchian_exit"]["lower"]
            last_low_closed_candle = previous_candle.low_price

            if donchian_lower > self._trailing_exit_level:
                self._log.info(
                    "Trailing updated",
                    previous=f"{self._trailing_exit_level:.2f}",
                    new=f"{donchian_lower:.2f}",
                )

                self._trailing_exit_level = donchian_lower

            elif last_low_closed_candle <= self._trailing_exit_level:
                self._log.info(
                    "Trailing exit triggered",
                    low=f"{last_low_closed_candle:.2f}",
                    exit_level=f"{self._trailing_exit_level:.2f}",
                )
                self.orderbook.close(order)

    def _get_current_atr(self) -> float:
        candle_service = self._candles.get(Timeframe.FOUR_HOURS)
        if not isinstance(candle_service, CandleService):
            return 0.0

        candles = candle_service.candles
        if len(candles) < self._MIN_CANDLES_REQUIRED:
            return 0.0

        closed_candle = candles[-2]
        if "atr" not in closed_candle.indicators:
            return 0.0

        return closed_candle.indicators["atr"]["value"]

    def _open_long_order(self, atr: float) -> None:
        if self._tick is None:
            return

        current_price = self._tick.close_price
        tp_multiplier = self._settings.get("take_profit_atr_multiplier", 2.5)
        sl_multiplier = self._settings.get("stop_loss_atr_multiplier", 1.5)
        trailing_enabled = self._settings.get("trailing_enabled", True)

        stop_loss_price = current_price - (sl_multiplier * atr)
        take_profit_price = 0.0 if trailing_enabled else current_price + (tp_multiplier * atr)

        volume_percentage = self._settings.get("volume_percentage", 0.05)
        volume = (self.nav / current_price) * volume_percentage

        self._atr_at_entry = atr
        self._trailing_active = False
        self._trailing_exit_level = stop_loss_price

        self.open_order(
            OrderSide.BUY,
            current_price,
            take_profit_price,
            stop_loss_price,
            volume,
            variables={
                "atr_at_entry": atr,
            },
        )

        message = (
            f"Opened LONG: price={current_price:.2f}, "
            f"sl={stop_loss_price:.2f}, tp={take_profit_price:.2f}, "
            f"atr={atr:.2f}, volume={volume:.6f}"
        )
        self._log.info(message)
