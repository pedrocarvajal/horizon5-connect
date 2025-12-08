"""RSI Bollinger Breakout trading strategy implementation."""

from typing import Any, Dict

from enums.order_side import OrderSide
from enums.order_status import OrderStatus
from enums.quality_method import QualityMethod
from enums.timeframe import Timeframe
from indicators.adx import ADXIndicator
from indicators.atr import ATRIndicator
from indicators.ma import MAIndicator
from indicators.rsi_bollinger_bands import RSIBollingerBandsIndicator
from models.backtest_expectation import BacktestExpectationModel
from models.order import OrderModel
from models.tick import TickModel
from services.candle import CandleService
from services.logging import LoggingService
from services.strategy import StrategyService


class RSIBollingerBreakoutStrategy(StrategyService):
    """Trading strategy based on RSI Bollinger Bands with trend and strength filters.

    Entry Rules:
    - RSI value is below lower Bollinger Band (RSI oversold relative to recent values)
    - ADX above threshold (trend strength confirmation)
    - Price closes above EMA (trend filter)
    - Only BUY orders (long-only strategy)

    Exit Rules:
    - Take profit: ATR multiplier above entry
    - Stop loss: ATR multiplier below entry

    Attributes:
        _enabled: Strategy activation flag.
        _name: Strategy identifier.
        _settings: Configuration parameters.
        _backtest_expectation: Expected thresholds for quality calculation.
        _candles: Candle services for the trading timeframe.
    """

    _MIN_CANDLES_REQUIRED: int = 2

    _enabled = False
    _name = "RSIBollingerBreakout"
    _settings: Dict[str, Any]

    def __init__(self, **kwargs: Any) -> None:
        """Initialize RSI Bollinger Breakout strategy with configuration.

        Args:
            **kwargs: Keyword arguments including optional 'settings' dict with:
                - volume_percentage: Order size as % of NAV (default: 1.0)
                - rsi_period: RSI period (default: 10)
                - adx_period: ADX period (default: 14)
                - ema_period: EMA period for trend filter (default: 150)
                - atr_period: ATR period (default: 20)
                - bollinger_period: Bollinger Bands period on RSI (default: 5)
                - bollinger_deviation: Bollinger Bands deviation (default: 1.7)
                - adx_threshold: Minimum ADX for trend strength (default: 25.0)
                - take_profit_atr_multiplier: ATR multiplier for TP (default: 3.5)
                - stop_loss_atr_multiplier: ATR multiplier for SL (default: 2.5)
        """
        super().__init__(**kwargs)

        self._log = LoggingService()

        self._backtest_quality_method = QualityMethod.FQS
        self._backtest_expectation = BacktestExpectationModel(
            num_trades=[5, 100],
            max_drawdown=[-0.25, -0.05],
            performance_percentage=[0.20, 1.00],
            sortino_ratio=[0.5, 3.0],
            profit_factor=[1.2, 3.0],
        )

        self._settings = kwargs.get(
            "settings",
            {
                "volume_percentage": 1.0,
                "rsi_period": 10,
                "adx_period": 14,
                "ema_period": 150,
                "atr_period": 20,
                "bollinger_period": 5,
                "bollinger_deviation": 1.7,
                "adx_threshold": 25.0,
                "take_profit_atr_multiplier": 3.5,
                "stop_loss_atr_multiplier": 2.5,
            },
        )

        rsi_period = self._settings.get("rsi_period", 10)
        adx_period = self._settings.get("adx_period", 14)
        ema_period = self._settings.get("ema_period", 150)
        atr_period = self._settings.get("atr_period", 20)
        bollinger_period = self._settings.get("bollinger_period", 5)
        bollinger_deviation = self._settings.get("bollinger_deviation", 1.7)

        self._candles = {
            Timeframe.FOUR_HOURS: CandleService(
                timeframe=Timeframe.FOUR_HOURS,
                indicators=[
                    RSIBollingerBandsIndicator(
                        key="rsi_bb",
                        rsi_period=rsi_period,
                        bollinger_period=bollinger_period,
                        deviation=bollinger_deviation,
                        price_to_use="close_price",
                    ),
                    ADXIndicator(
                        key="adx",
                        period=adx_period,
                    ),
                    MAIndicator(
                        key="ema",
                        period=ema_period,
                        price_to_use="close_price",
                        is_exponential=True,
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
        """Handle new hour event - check entry on 4H candle close."""
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

        self._check_entry_conditions()

    def on_transaction(self, order: OrderModel) -> None:
        """Handle order transaction events and log status changes.

        Args:
            order: Order that triggered the transaction event.
        """
        super().on_transaction(order)

        if order.status.is_open():
            self._log.info(f"Order: {order.id}, was opened at price {order.price:.2f}")

        if order.status.is_closed():
            profit_percentage = order.profit_percentage * 100
            profit = order.profit

            self._log.info(f"Order: {order.id}, was closed, profit: {profit:.2f} ({profit_percentage:.2f}%)")

    def _check_entry_conditions(self) -> None:
        assert self._tick is not None

        candle_service = self._candles.get(Timeframe.FOUR_HOURS)
        if not isinstance(candle_service, CandleService):
            return

        candles = candle_service.candles
        if len(candles) < self._MIN_CANDLES_REQUIRED:
            return

        closed_candle = candles[-2]

        if "rsi_bb" not in closed_candle.indicators:
            return
        if "adx" not in closed_candle.indicators:
            return
        if "ema" not in closed_candle.indicators:
            return
        if "atr" not in closed_candle.indicators:
            return

        if len(self.orderbook.where(side=OrderSide.BUY, status=OrderStatus.OPEN)) > 0:
            return

        rsi_value = closed_candle.indicators["rsi_bb"]["rsi_value"]
        lower_band = closed_candle.indicators["rsi_bb"]["lower_band"]
        current_adx = closed_candle.indicators["adx"]["adx"]
        current_ema = closed_candle.indicators["ema"]["value"]
        current_atr = closed_candle.indicators["atr"]["value"]
        current_close = closed_candle.close_price

        adx_threshold = self._settings.get("adx_threshold", 25.0)

        condition_rsi_oversold = rsi_value < lower_band
        condition_strength = current_adx > adx_threshold
        condition_trend = current_close > current_ema

        if condition_rsi_oversold and condition_strength and condition_trend:
            message = (
                f"RSI_BB SIGNAL: rsi={rsi_value:.2f} < lower_band={lower_band:.2f}, "
                f"adx={current_adx:.2f} > {adx_threshold}, "
                f"close={current_close:.2f} > ema={current_ema:.2f}"
            )
            self._log.info(message)
            self._open_long_order(current_atr)

    def _open_long_order(self, atr: float) -> None:
        assert self._tick is not None

        current_price = self._tick.price
        tp_multiplier = self._settings.get("take_profit_atr_multiplier", 3.5)
        sl_multiplier = self._settings.get("stop_loss_atr_multiplier", 2.5)

        stop_loss_price = current_price - (sl_multiplier * atr)
        take_profit_price = current_price + (tp_multiplier * atr)

        volume_percentage = self._settings.get("volume_percentage", 1.0)
        volume = (self.nav / current_price) * volume_percentage

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
