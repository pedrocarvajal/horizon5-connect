import datetime
from typing import Any, Dict

from enums.timeframe import Timeframe
from interfaces.analytic import AnalyticInterface
from interfaces.candle import CandleInterface
from interfaces.indicator import IndicatorInterface
from interfaces.strategy import StrategyInterface
from models.order import OrderModel
from models.tick import TickModel
from services.analytic import AnalyticService
from services.asset import AssetService
from services.logging import LoggingService

from .handlers.orderbook import OrderbookHandler
from .helpers.get_truncated_timeframe import get_truncated_timeframe


class StrategyService(StrategyInterface):
    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    _backtest: bool
    _asset: AssetService
    _allocation: float
    _indicators: Dict[str, IndicatorInterface]
    _candles: Dict[Timeframe, CandleInterface]
    _orderbook: OrderbookHandler
    _analytic: AnalyticInterface
    _last_timestamps: Dict[Timeframe, datetime.datetime]
    _tick: TickModel

    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(self, **kwargs: Any) -> None:
        self._log = LoggingService()
        self._log.setup("strategy_service")

        self._backtest = False
        self._indicators = {}
        self._candles = {}
        self._orderbook = None
        self._analytic = None
        self._last_timestamps = {}
        self._allocation = kwargs.get("allocation", 0.0)

    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def setup(self, **kwargs: Any) -> None:
        self._asset = kwargs.get("asset")
        self._backtest = kwargs.get("backtest", False)

        if self._asset is None:
            raise ValueError("Asset is required")

        if self._allocation <= 0:
            raise ValueError("Allocation must be greater than 0")

        self._orderbook = OrderbookHandler(
            balance=self._allocation,
            allocation=self._allocation,
            on_transaction=self.on_transaction,
        )

        self._analytic = AnalyticService(
            orderbook=self._orderbook,
        )

        self._log.info(f"Setting up {self.name}")

    def on_tick(self, tick: TickModel) -> None:
        self._tick = tick
        self._check_timeframe_transitions(tick)
        self._orderbook.refresh(tick)
        self._analytic.on_tick(tick)

        for indicator in self._indicators.values():
            indicator.on_tick(tick)

        for candle in self._candles.values():
            candle.on_tick(tick)

    def on_new_hour(self) -> None:
        self._analytic.on_new_hour()

    def on_new_day(self) -> None:
        self._orderbook.clean()
        self._analytic.on_new_day()

    def on_new_week(self) -> None:
        self._analytic.on_new_week()

    def on_new_month(self) -> None:
        self._analytic.on_new_month()

    def on_transaction(self, order: OrderModel) -> None:
        self._analytic.on_transaction(order)

    def on_end(self) -> None:
        if self._backtest:
            self._log.info("Backtest mode detected, closing all orders.")

            for order in self._orderbook.orders:
                self._orderbook.close(order)

        self._analytic.on_end()

    # ───────────────────────────────────────────────────────────
    # PRIVATE METHODS
    # ───────────────────────────────────────────────────────────
    def _check_timeframe_transitions(self, tick: TickModel) -> None:
        current_time = tick.date

        for timeframe in Timeframe:
            last_timestamp = self._last_timestamps.get(timeframe)

            if last_timestamp is None:
                self._last_timestamps[timeframe] = get_truncated_timeframe(
                    current_time, timeframe
                )
                continue

            current_period = get_truncated_timeframe(current_time, timeframe)

            if current_period > last_timestamp:
                self._last_timestamps[timeframe] = current_period
                self._trigger_timeframe_event(timeframe)

    def _trigger_timeframe_event(self, timeframe: Timeframe) -> None:
        if timeframe == Timeframe.ONE_MINUTE:
            self.on_new_minute()

        elif timeframe == Timeframe.ONE_HOUR:
            self.on_new_hour()

        elif timeframe == Timeframe.ONE_DAY:
            self.on_new_day()

        elif timeframe == Timeframe.ONE_WEEK:
            self.on_new_week()

        elif timeframe == Timeframe.ONE_MONTH:
            self.on_new_month()

    # ───────────────────────────────────────────────────────────
    # GETTERS
    # ───────────────────────────────────────────────────────────
    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def name(self) -> str:
        return self._name

    @property
    def asset(self) -> AssetService:
        return self._asset

    @property
    def orderbook(self) -> OrderbookHandler:
        return self._orderbook

    @property
    def allocation(self) -> float:
        return self._allocation
