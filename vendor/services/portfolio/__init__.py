"""Portfolio service for managing collections of trading assets."""

from __future__ import annotations

import datetime
from multiprocessing import Queue
from typing import Any, Dict, List, Optional

from vendor.enums.timeframe import Timeframe
from vendor.interfaces.analytic import AnalyticInterface
from vendor.interfaces.asset import AssetInterface
from vendor.interfaces.portfolio import AssetConfig, PortfolioInterface
from vendor.models.tick import TickModel
from vendor.services.analytic import PortfolioAnalytic
from vendor.services.logging import LoggingService
from vendor.services.strategy.helpers.get_truncated_timeframe import get_truncated_timeframe


class PortfolioService(PortfolioInterface):
    """Service for managing a portfolio of trading assets."""

    _analytic: Optional[AnalyticInterface]
    _assets: List[AssetConfig]
    _asset_instances: List[AssetInterface]
    _backtest: bool
    _backtest_id: Optional[str]
    _commands_queue: Optional[Queue[Any]]
    _events_queue: Optional[Queue[Any]]
    _id: str
    _last_timestamps: Dict[Timeframe, datetime.datetime]
    _log: LoggingService

    def __init__(self) -> None:
        """Initialize the portfolio with an empty asset list."""
        self._analytic = None
        self._assets = []
        self._asset_instances = []
        self._backtest = False
        self._backtest_id = None
        self._commands_queue = None
        self._events_queue = None
        self._id = ""
        self._last_timestamps = {}
        self._log = LoggingService()

    def on_end(self) -> Dict[str, Any]:
        """Finalize portfolio and return aggregated report."""
        if self._analytic is None:
            return {}

        report = self._analytic.on_end()
        return report if report is not None else {}

    def on_new_day(self) -> None:
        """Handle a new day event. Cascades to all assets."""
        for asset in self._asset_instances:
            asset.on_new_day()

        if self._analytic is not None:
            self._analytic.on_new_day()

    def on_new_hour(self) -> None:
        """Handle a new hour event. Cascades to all assets."""
        for asset in self._asset_instances:
            asset.on_new_hour()

        if self._analytic is not None:
            self._analytic.on_new_hour()

    def on_new_minute(self) -> None:
        """Handle a new minute event. Cascades to all assets."""
        for asset in self._asset_instances:
            asset.on_new_minute()

    def on_new_month(self) -> None:
        """Handle a new month event. Cascades to all assets."""
        for asset in self._asset_instances:
            asset.on_new_month()

        if self._analytic is not None:
            self._analytic.on_new_month()

    def on_new_week(self) -> None:
        """Handle a new week event. Cascades to all assets."""
        for asset in self._asset_instances:
            asset.on_new_week()

        if self._analytic is not None:
            self._analytic.on_new_week()

    def on_tick(self, ticks: Dict[str, TickModel]) -> None:
        """Process tick data for all assets.

        Args:
            ticks: Dictionary mapping symbol to tick data.
        """
        last_tick: Optional[TickModel] = None

        for asset in self._asset_instances:
            tick = ticks.get(asset.symbol)

            if tick is not None:
                asset.on_tick(tick)

                if self._analytic is not None:
                    self._analytic.on_tick(tick)

                last_tick = tick

        if last_tick is not None:
            self._check_timeframe_transitions(last_tick)

    def setup(self, **kwargs: Any) -> None:
        """Configure the portfolio and instantiate all assets."""
        self._backtest = kwargs.get("backtest", False)
        self._backtest_id = kwargs.get("backtest_id")
        self._commands_queue = kwargs.get("commands_queue")
        self._events_queue = kwargs.get("events_queue")

        if self._commands_queue is None:
            raise ValueError("Commands queue is required")

        if self._events_queue is None:
            raise ValueError("Events queue is required")

        for asset_config in self._assets:
            asset_class = asset_config["asset"]
            allocation = asset_config["allocation"]
            enabled = asset_config.get("enabled", True)

            if not enabled:
                self._log.warning(f"Asset {asset_class.__name__} is disabled in portfolio config")
                continue

            asset_instance = asset_class(allocation=allocation, enabled=enabled)

            asset_instance.setup(**kwargs)
            self._asset_instances.append(asset_instance)

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

        if self._commands_queue is None or self._events_queue is None:
            return

        self._analytic = PortfolioAnalytic(
            portfolio_id=self._id,
            assets=self._asset_instances,
            backtest=self._backtest,
            backtest_id=self._backtest_id,
            commands_queue=self._commands_queue,
        )

    def _check_timeframe_transitions(self, tick: TickModel) -> None:
        """Check for timeframe transitions and trigger appropriate events."""
        current_time = tick.date

        for timeframe in Timeframe:
            last_timestamp = self._last_timestamps.get(timeframe)

            if last_timestamp is None:
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
