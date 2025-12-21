"""Meb Faber Timing strategy implementation based on 10-month SMA crossover."""

from typing import Any, ClassVar, Dict, List, Optional

from vendor.enums.order_side import OrderSide
from vendor.enums.order_status import OrderStatus
from vendor.enums.quality_method import QualityMethod
from vendor.enums.timeframe import Timeframe
from vendor.indicators.ma import MAIndicator
from vendor.models.backtest_expectation import BacktestExpectationModel
from vendor.models.order import OrderModel
from vendor.models.tick import TickModel
from vendor.services.candle import CandleService
from vendor.services.strategy import StrategyService


class MebFaberTimingStrategy(StrategyService):
    """Trading strategy based on Meb Faber's Tactical Asset Allocation.

    This strategy implements the timing model from Faber's paper
    "A Quantitative Approach to Tactical Asset Allocation" (2006).

    Entry Rules:
    - BUY when monthly close price > SMA(10 months)
    - Only evaluated at end of month (on_new_month event)
    - Long-only strategy (no shorting)

    Exit Rules:
    - SELL (close position) when monthly close price < SMA(10 months)
    - No fixed take profit or stop loss
    - Exit only based on SMA crossover signal

    Key Characteristics:
    - Monthly rebalancing only (ignores intra-month price action)
    - Binary: either 100% invested or 100% cash
    - Designed to reduce drawdowns while capturing major trends
    - Historical performance: ~70% time in market, ~1 trade/year

    Attributes:
        _enabled: Strategy activation flag.
        _name: Strategy identifier.
        _settings: Configuration parameters.
        _candles: Candle services for the trading timeframe.
        _is_invested: Current investment state (in market or cash).
    """

    _MIN_CANDLES_REQUIRED: int = 11
    _DEFAULT_SETTINGS: ClassVar[Dict[str, Any]] = {
        "volume_percentage": 1.0,
        "sma_period": 10,
    }

    _enabled = True
    _name = "MebFaberTiming"
    _settings: Dict[str, Any]

    def __init__(self, **kwargs: Any) -> None:
        """Initialize Meb Faber Timing strategy with configuration.

        Args:
            **kwargs: Keyword arguments including optional 'settings' dict with:
                - volume_percentage: Percentage of NAV to invest (default: 1.0 = 100%)
                - sma_period: SMA period in months (default: 10)
        """
        super().__init__(**kwargs)

        self._backtest_quality_method = QualityMethod.FQS
        self._backtest_expectation = BacktestExpectationModel(
            max_drawdown=[-0.25, 0],
            performance_percentage=[0.05, 1],
            r_squared=[0, 1],
        )

        settings = kwargs.get("settings", {})
        self._settings = {**self._DEFAULT_SETTINGS, **settings}

        self._is_invested: bool = False
        self._last_signal_date: Optional[str] = None

        sma_period = self._settings.get("sma_period", 10)

        self._candles = {
            Timeframe.ONE_MONTH: CandleService(
                timeframe=Timeframe.ONE_MONTH,
                indicators=[
                    MAIndicator(
                        key="sma",
                        period=sma_period,
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

    def on_new_month(self) -> None:
        """Handle new month event - evaluate timing signal.

        This is the core of Faber's strategy: only evaluate and act
        at the end of each month based on SMA crossover.
        """
        super().on_new_month()
        self._evaluate_timing_signal()

    def on_transaction(self, order: OrderModel) -> None:
        """Handle order transaction events.

        Args:
            order: Order that triggered the transaction event.
        """
        super().on_transaction(order)

        if order.status.is_open():
            self._is_invested = True
            self._log.info(
                "Position opened (entered market)",
                order_id=order.id,
                price=f"{order.price:.2f}",
            )

        if order.status.is_closed():
            profit_percentage = order.profit_percentage * 100

            self._log.info(
                "Position closed (exited to cash)",
                order_id=order.id,
                profit=f"{order.profit:.2f}",
                profit_percentage=f"{profit_percentage:.2f}%",
            )

            open_orders = self._get_open_orders()
            if len(open_orders) == 0:
                self._is_invested = False

    def _get_open_orders(self, side: Optional[OrderSide] = None) -> List[OrderModel]:
        if side:
            return self.orderbook.where(side=side, status=OrderStatus.OPEN)
        return self.orderbook.where(status=OrderStatus.OPEN)

    def _evaluate_timing_signal(self) -> None:
        if not self._tick:
            return

        candle_service = self._candles.get(Timeframe.ONE_MONTH)
        if not candle_service:
            return

        candles = candle_service.candles
        if len(candles) < self._MIN_CANDLES_REQUIRED:
            return

        closed_candle = candles[-2]

        if "sma" not in closed_candle.indicators:
            return

        close_price = closed_candle.close_price
        sma_value = closed_candle.indicators["sma"]["value"]

        if not sma_value or sma_value <= 0:
            return

        current_month = self._tick.date.strftime("%Y-%m")
        if self._last_signal_date == current_month:
            return

        self._last_signal_date = current_month

        is_above_sma = close_price > sma_value
        open_orders = self._get_open_orders()
        has_position = len(open_orders) > 0

        self._log.info(
            "Monthly evaluation",
            close_price=f"{close_price:.2f}",
            sma=f"{sma_value:.2f}",
            signal="BULLISH" if is_above_sma else "BEARISH",
            position="INVESTED" if has_position else "CASH",
        )

        if is_above_sma and not has_position:
            self._open_position()

        elif not is_above_sma and has_position:
            self._close_all_positions()

    def _open_position(self) -> None:
        if not self._tick:
            return

        current_price = self._tick.close_price
        volume_percentage = self._settings.get("volume_percentage", 1.0)

        volume = (self.nav / current_price) * volume_percentage

        self._log.info(
            "Opening long position (price > SMA)",
            price=f"{current_price:.2f}",
            volume=f"{volume:.6f}",
            nav=f"{self.nav:.2f}",
        )

        self.open_order(
            OrderSide.BUY,
            current_price,
            0.0,
            0.0,
            volume,
            variables={"entry_reason": "sma_crossover_bullish"},
        )

    def _close_all_positions(self) -> None:
        open_orders = self._get_open_orders()

        for order in open_orders:
            current_price_str = f"{self._tick.close_price:.2f}" if self._tick else "N/A"
            self._log.info(
                "Closing position (price < SMA)",
                order_id=order.id,
                entry_price=f"{order.price:.2f}",
                current_price=current_price_str,
            )
            self.orderbook.close(order)
