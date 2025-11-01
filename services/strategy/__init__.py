import datetime
from typing import Any, Dict

from enums.timeframe import Timeframe
from interfaces.candle import CandleInterface
from interfaces.indicator import IndicatorInterface
from interfaces.strategy import StrategyInterface
from models.tick import TickModel
from services.asset import AssetService
from services.logging import LoggingService

from .handlers.orderbook import OrderbookHandler
from .helpers.get_truncated_timeframe import get_truncated_timeframe


class StrategyService(StrategyInterface):
    _indicators: Dict[str, IndicatorInterface]
    _candles: Dict[Timeframe, CandleInterface]
    _orderbook: OrderbookHandler
    _last_timestamps: Dict[Timeframe, datetime.datetime]

    def __init__(self) -> None:
        super().__init__()

        self._log = LoggingService()
        self._log.setup("strategy_service")

        self._indicators = {}
        self._candles = {}
        self._last_timestamps = {}
        self._orderbook = None

    def setup(self, **kwargs: Any) -> None:
        self._asset = kwargs.get("asset")

        if self._asset is None:
            raise ValueError("Asset is required")

        self._orderbook = OrderbookHandler(
            on_transaction=self.on_transaction,
        )

        self._log.info(f"Setting up {self.name}")

    def on_tick(self, tick: TickModel) -> None:
        self._check_timeframe_transitions(tick)
        self._orderbook.refresh(tick)

        for indicator in self._indicators.values():
            indicator.on_tick(tick)

        for candle in self._candles.values():
            candle.on_tick(tick)

    def on_new_minute(self, tick: TickModel) -> None:
        pass

    def on_new_hour(self, tick: TickModel) -> None:
        pass

    def on_new_day(self, tick: TickModel) -> None:
        self._orderbook.clean()

    def on_new_week(self, tick: TickModel) -> None:
        pass

    def on_new_month(self, tick: TickModel) -> None:
        pass

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
                self._trigger_timeframe_event(timeframe, tick)

    def _trigger_timeframe_event(self, timeframe: Timeframe, tick: TickModel) -> None:
        if timeframe == Timeframe.ONE_MINUTE:
            self.on_new_minute(tick)

        elif timeframe == Timeframe.ONE_HOUR:
            self.on_new_hour(tick)

        elif timeframe == Timeframe.ONE_DAY:
            self.on_new_day(tick)

        elif timeframe == Timeframe.ONE_WEEK:
            self.on_new_week(tick)

        elif timeframe == Timeframe.ONE_MONTH:
            self.on_new_month(tick)

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
