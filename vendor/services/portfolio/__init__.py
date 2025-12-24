"""Portfolio service for managing collections of trading assets."""

from __future__ import annotations

import datetime
from multiprocessing import Queue
from typing import Any, Dict, List, Optional

from vendor.enums.timeframe import Timeframe
from vendor.helpers.get_asset_by_path import get_asset_by_path
from vendor.helpers.get_slug import get_slug
from vendor.interfaces.analytic import AnalyticInterface
from vendor.interfaces.asset import AssetInterface
from vendor.interfaces.logging import LoggingInterface
from vendor.interfaces.portfolio import PortfolioInterface
from vendor.models.tick import TickModel
from vendor.services.analytic import PortfolioAnalytic
from vendor.services.logging import LoggingService
from vendor.services.strategy.helpers.get_truncated_timeframe import get_truncated_timeframe


class PortfolioService(PortfolioInterface):
    """Service for managing a portfolio of trading assets."""

    _id: str
    _name: str
    _allocation: float
    _assets: List[AssetInterface]

    _analytic: Optional[AnalyticInterface]
    _backtest: bool
    _backtest_id: Optional[str]
    _commands_queue: Optional[Queue[Any]]
    _events_queue: Optional[Queue[Any]]
    _last_timestamps: Dict[Timeframe, datetime.datetime]
    _log: LoggingInterface

    def __init__(self, name: str, allocation: float, assets: List[str]) -> None:
        """Initialize the portfolio with an empty asset list."""
        self._name = name
        self._id = get_slug(self._name)
        self._allocation = allocation
        self._assets = [get_asset_by_path(path)() for path in assets]

        self._last_timestamps = {}

        self._analytic = None
        self._backtest = False
        self._backtest_id = None
        self._commands_queue = None
        self._events_queue = None

        self._log = LoggingService()

    def on_end(self) -> Dict[str, Any]:
        """Finalize portfolio and return aggregated report."""
        if not self._analytic:
            return {}

        report = self._analytic.on_end()
        return report if report else {}

    def on_new_day(self) -> None:
        """Handle a new day event. Cascades to all assets."""
        for asset in self._assets:
            asset.on_new_day()

        if self._analytic:
            self._analytic.on_new_day()

    def on_new_hour(self) -> None:
        """Handle a new hour event. Cascades to all assets."""
        for asset in self._assets:
            asset.on_new_hour()

        if self._analytic:
            self._analytic.on_new_hour()

    def on_new_minute(self) -> None:
        """Handle a new minute event. Cascades to all assets."""
        for asset in self._assets:
            asset.on_new_minute()

    def on_new_month(self) -> None:
        """Handle a new month event. Cascades to all assets."""
        for asset in self._assets:
            asset.on_new_month()

        if self._analytic:
            self._analytic.on_new_month()

    def on_new_week(self) -> None:
        """Handle a new week event. Cascades to all assets."""
        for asset in self._assets:
            asset.on_new_week()

        if self._analytic:
            self._analytic.on_new_week()

    def on_tick(self, ticks: Dict[str, TickModel]) -> None:
        """Process tick data for all assets.

        Args:
            ticks: Dictionary mapping symbol to tick data.
        """
        last_tick: Optional[TickModel] = None

        for asset in self._assets:
            tick = ticks.get(asset.symbol)

            if tick:
                asset.on_tick(tick)

                if self._analytic:
                    self._analytic.on_tick(tick)

                last_tick = tick

        if last_tick:
            self._check_timeframe_transitions(last_tick)

    def setup(self, **kwargs: Any) -> None:
        """Configure the portfolio name and/or runtime parameters.

        Args:
            **kwargs: Configuration parameters including:
                name: Display name for the portfolio (generates ID via slug).
                backtest: Whether running in backtest mode.
                backtest_id: Backtest identifier.
                commands_queue: Queue for commands.
                events_queue: Queue for events.
        """
        commands_queue = kwargs.get("commands_queue")
        events_queue = kwargs.get("events_queue")

        if commands_queue is None and events_queue is None:
            return

        if commands_queue is None:
            raise ValueError("Commands queue is required")

        if events_queue is None:
            raise ValueError("Events queue is required")

        if not self._allocation or self._allocation <= 0:
            raise ValueError("Allocation is required")

        if len(self._assets) == 0:
            raise ValueError("Assets is required")

        if len(self._name) == 0:
            raise ValueError("Name is required")

        self._backtest = kwargs.get("backtest", False)
        self._backtest_id = kwargs.get("backtest_id")
        self._commands_queue = commands_queue
        self._events_queue = events_queue

        for asset in self._assets:
            asset.allocation = self._allocation / len(self._assets)
            asset.setup(portfolio=self, **kwargs)

        self.setup_analytic()

    def setup_analytic(self, **kwargs: Any) -> None:
        """Initialize the portfolio analytics service.

        This method can be called separately when assets are setup externally
        (e.g., by BacktestService for parallel downloads).

        Args:
            **kwargs: Configuration parameters including:
                backtest: Whether running in backtest mode.
                backtest_id: Backtest identifier.
                commands_queue: Queue for commands.
                events_queue: Queue for events.
        """
        if kwargs:
            self._backtest = kwargs.get("backtest", self._backtest)
            self._backtest_id = kwargs.get("backtest_id", self._backtest_id)
            self._commands_queue = kwargs.get("commands_queue", self._commands_queue)
            self._events_queue = kwargs.get("events_queue", self._events_queue)

        if not self._commands_queue or not self._events_queue:
            return

        self._analytic = PortfolioAnalytic(
            portfolio_id=self._id,
            assets=self.assets,
            backtest=self._backtest,
            backtest_id=self._backtest_id,
            commands_queue=self._commands_queue,
        )

    def _check_timeframe_transitions(self, tick: TickModel) -> None:
        """Check for timeframe transitions and trigger appropriate events."""
        current_time = tick.date

        for timeframe in Timeframe:
            last_timestamp = self._last_timestamps.get(timeframe)

            if not last_timestamp:
                self._last_timestamps[timeframe] = get_truncated_timeframe(current_time, timeframe)
                continue

            current_period = get_truncated_timeframe(current_time, timeframe)

            if current_period > last_timestamp:
                self._last_timestamps[timeframe] = current_period
                self._trigger_timeframe_event(timeframe)

    def _trigger_timeframe_event(self, timeframe: Timeframe) -> None:
        """Trigger the appropriate event handler for a timeframe transition."""
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
