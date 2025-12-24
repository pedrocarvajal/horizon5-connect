"""IBS (Internal Bar Strength) mean reversion strategy implementation."""

from typing import Any, ClassVar, Dict, List, Optional

from indicators.adx import ADXIndicator
from indicators.ibs import IBSIndicator
from vendor.enums.order_side import OrderSide
from vendor.enums.order_status import OrderStatus
from vendor.enums.quality_method import QualityMethod
from vendor.enums.timeframe import Timeframe
from vendor.models.backtest_expectation import BacktestExpectationModel
from vendor.models.order import OrderModel
from vendor.models.tick import TickModel
from vendor.services.candle import CandleService
from vendor.services.strategy import StrategyService


class IBSStrategy(StrategyService):
    """Mean reversion strategy based on Internal Bar Strength (IBS).

    IBS = (Close - Low) / (High - Low)

    Entry Rules:
    - BUY when daily IBS falls below threshold (default 0.15)
    - ADX must be above adx_threshold (confirms trend strength for stronger bounce)
    - Signal evaluated at end of day (on_new_day event)

    Exit Rules:
    - Exit at next day open if position shows profit
    - Exit after max_holding_bars regardless of profitability
    - No fixed take profit or stop loss

    Key Characteristics:
    - Daily timeframe mean reversion strategy
    - Short holding period (1-3 days typical)
    - Works best on index futures (Nasdaq, S&P 500)
    - ADX filter improves win rate significantly
    """

    _MIN_CANDLES_REQUIRED: int = 30
    _DEFAULT_SETTINGS: ClassVar[Dict[str, Any]] = {
        "volume_percentage": 1.0,
        "ibs_threshold": 0.20,
        "max_holding_bars": 5,
        "adx_period": 14,
        "adx_threshold": 20.0,
        "use_adx_filter": True,
        "stop_loss_percentage": 0.03,
    }

    _name = "IBS"
    _settings: Dict[str, Any]

    def __init__(self, **kwargs: Any) -> None:
        """Initialize IBS strategy with configuration."""
        super().__init__(**kwargs)

        self._backtest_quality_method = QualityMethod.FQS
        self._backtest_expectation = BacktestExpectationModel(
            max_drawdown=[-0.20, 0],
            performance_percentage=[0.15, 1],
            r_squared=[0, 1],
        )

        settings = kwargs.get("settings", {})
        self._settings = {**self._DEFAULT_SETTINGS, **settings}

        self._pending_entry: bool = False
        self._bars_held: int = 0
        self._entry_date: Optional[str] = None

        adx_period = self._settings.get("adx_period", 14)

        self._candles = {
            Timeframe.ONE_DAY: CandleService(
                timeframe=Timeframe.ONE_DAY,
                indicators=[
                    IBSIndicator(key="ibs"),
                    ADXIndicator(key="adx", period=adx_period),
                ],
            )
        }

    def on_tick(self, tick: TickModel) -> None:
        """Process incoming tick."""
        super().on_tick(tick)
        self._tick = tick

    def on_new_day(self) -> None:
        """Handle new day event - evaluate IBS signal and manage positions."""
        super().on_new_day()

        open_orders = self._get_open_orders()

        if len(open_orders) > 0:
            self._bars_held += 1
            self._check_exit_conditions()
        elif self._pending_entry:
            self._execute_entry()
        else:
            self._evaluate_ibs_signal()

    def on_transaction(self, order: OrderModel) -> None:
        """Handle order transaction events."""
        super().on_transaction(order)

        if order.status.is_open():
            self._bars_held = 0
            self._pending_entry = False
            self._log.info(
                "IBS position opened",
                order_id=order.id,
                price=f"{order.price:.2f}",
            )

        if order.status.is_closed():
            profit_percentage = order.profit_percentage * 100

            self._log.info(
                "IBS position closed",
                order_id=order.id,
                profit=f"{order.profit:.2f}",
                profit_percentage=f"{profit_percentage:.2f}%",
                bars_held=self._bars_held,
            )

            self._bars_held = 0

    def _get_open_orders(self, side: Optional[OrderSide] = None) -> List[OrderModel]:
        if side:
            return self.orderbook.where(side=side, status=OrderStatus.OPEN)
        return self.orderbook.where(status=OrderStatus.OPEN)

    def _evaluate_ibs_signal(self) -> None:
        if not self._tick:
            return

        candle_service = self._candles.get(Timeframe.ONE_DAY)
        if not candle_service:
            return

        candles = candle_service.candles
        if len(candles) < self._MIN_CANDLES_REQUIRED:
            return

        closed_candle = candles[-2]

        if "ibs" not in closed_candle.indicators:
            return

        ibs_value = closed_candle.indicators["ibs"]["value"]

        if ibs_value is None:
            return

        ibs_threshold = self._settings.get("ibs_threshold", 0.15)
        use_adx_filter = self._settings.get("use_adx_filter", True)
        adx_threshold = self._settings.get("adx_threshold", 25.0)

        current_date = self._tick.date.strftime("%Y-%m-%d")

        if self._entry_date == current_date:
            return

        is_oversold = ibs_value < ibs_threshold
        adx_value = 0.0
        adx_valid = True

        if use_adx_filter and "adx" in closed_candle.indicators:
            adx_value = closed_candle.indicators["adx"].get("adx", 0.0)
            if adx_value is None:
                adx_value = 0.0
            adx_valid = adx_value >= adx_threshold

        should_buy = is_oversold and adx_valid

        self._log.info(
            "Daily IBS evaluation",
            date=current_date,
            close_price=f"{closed_candle.close_price:.2f}",
            ibs=f"{ibs_value:.4f}",
            ibs_threshold=f"{ibs_threshold:.2f}",
            adx=f"{adx_value:.2f}",
            adx_threshold=f"{adx_threshold:.1f}",
            signal="BUY" if should_buy else "HOLD",
        )

        if should_buy:
            self._pending_entry = True
            self._entry_date = current_date

    def _execute_entry(self) -> None:
        if not self._tick:
            return

        current_price = self._tick.close_price
        volume_percentage = self._settings.get("volume_percentage", 1.0)

        volume = (self.nav / current_price) * volume_percentage

        self._log.info(
            "Executing IBS entry",
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
            variables={"entry_reason": "ibs_oversold"},
        )

        self._pending_entry = False

    def _check_exit_conditions(self) -> None:
        if not self._tick:
            return

        open_orders = self._get_open_orders()
        max_holding_bars = self._settings.get("max_holding_bars", 5)
        stop_loss_pct = self._settings.get("stop_loss_percentage", 0.03)

        for order in open_orders:
            current_price = self._tick.close_price
            price_change = (current_price - order.price) / order.price

            is_profitable = current_price > order.price
            max_bars_reached = self._bars_held >= max_holding_bars
            stop_loss_hit = price_change <= -stop_loss_pct

            if is_profitable or max_bars_reached or stop_loss_hit:
                if stop_loss_hit:
                    exit_reason = "stop_loss"
                elif is_profitable:
                    exit_reason = "profitable"
                else:
                    exit_reason = "max_bars_reached"

                self._log.info(
                    f"Closing IBS position ({exit_reason})",
                    order_id=order.id,
                    entry_price=f"{order.price:.2f}",
                    current_price=f"{current_price:.2f}",
                    price_change=f"{price_change * 100:.2f}%",
                    bars_held=self._bars_held,
                )

                self.orderbook.close(order)
