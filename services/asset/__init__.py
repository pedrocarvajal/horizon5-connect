"""Asset service for managing trading strategies on a specific instrument."""

from __future__ import annotations

import datetime
from multiprocessing import Queue
from typing import Any, Dict, Optional

from enums.asset_quality_method import AssetQualityMethod
from enums.timeframe import Timeframe
from interfaces.asset import AssetInterface
from interfaces.portfolio import PortfolioInterface
from models.tick import TickModel
from services.asset.components import AnalyticComponent
from services.gateway import GatewayService
from services.logging import LoggingService
from services.quality_calculator import QualityCalculatorService
from services.strategy.helpers.get_truncated_timeframe import get_truncated_timeframe


class AssetService(AssetInterface):
    """Service managing strategies and gateway for a specific trading asset."""

    _asset_quality_method: AssetQualityMethod
    _backtest: bool
    _backtest_id: Optional[str]
    _commands_queue: Optional[Queue[Any]]
    _events_queue: Optional[Queue[Any]]
    _gateway_name: str
    _last_timestamps: Dict[Timeframe, datetime.datetime]
    _portfolio: Optional[PortfolioInterface]
    _tick: Optional[TickModel]

    _analytic: AnalyticComponent
    _log: LoggingService
    _quality_calculator: QualityCalculatorService

    def __init__(self, allocation: float = 0.0, enabled: bool = True) -> None:
        """Initialize the asset service with default configuration.

        Args:
            allocation: Total allocation for this asset to distribute among strategies.
            enabled: Whether this asset is enabled for execution.
        """
        self._log = LoggingService()

        self._allocation = allocation
        self._enabled = enabled
        self._strategies = []
        self._commands_queue = None
        self._events_queue = None
        self._backtest = False
        self._backtest_id = None
        self._portfolio = None
        self._is_historical_filling = False
        self._last_timestamps = {}
        self._tick = None

        if not hasattr(self, "_asset_quality_method"):
            self._asset_quality_method = AssetQualityMethod.WEIGHTED_AVERAGE

        self._quality_calculator = QualityCalculatorService(
            quality_method=self._asset_quality_method,
            children_key="strategies",
        )
        self._gateway = GatewayService(
            gateway=self._gateway_name,
            sandbox=False,
        )

    def on_end(self) -> Dict[str, Any]:
        """Notify all strategies that execution has ended.

        Returns:
            Asset report with aggregated performance and strategy reports.
        """
        self._quality_calculator.reset()

        for strategy in self._strategies:
            strategy_report = strategy.on_end()

            if strategy_report is not None:
                self._quality_calculator.on_report(strategy.id, strategy_report)

        return self._quality_calculator.on_end()

    def on_tick(self, tick: TickModel) -> None:
        """Propagate tick data to all enabled strategies."""
        self._tick = tick

        for strategy in self._strategies:
            strategy.on_tick(tick)

        self._analytic.on_tick(tick)
        self._check_timeframe_transitions(tick)

    def on_new_hour(self) -> None:
        """Handle a new hour event for asset-level analytics."""
        self._analytic.on_new_hour()

    def on_new_day(self) -> None:
        """Handle a new day event for asset-level analytics."""
        self._analytic.on_new_day()

    def on_new_week(self) -> None:
        """Handle a new week event for asset-level analytics."""
        self._analytic.on_new_week()

    def on_new_month(self) -> None:
        """Handle a new month event for asset-level analytics."""
        self._analytic.on_new_month()

    def _check_timeframe_transitions(self, tick: TickModel) -> None:
        """Check for timeframe transitions and trigger appropriate events."""
        current_time = tick.date

        for timeframe in Timeframe:
            if timeframe == Timeframe.ONE_MINUTE:
                continue

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
        if timeframe == Timeframe.ONE_HOUR:
            self.on_new_hour()

        elif timeframe == Timeframe.ONE_DAY:
            self.on_new_day()

        elif timeframe == Timeframe.ONE_WEEK:
            self.on_new_week()

        elif timeframe == Timeframe.ONE_MONTH:
            self.on_new_month()

    def setup(self, **kwargs: Any) -> None:
        """Configure the asset with runtime parameters and initialize strategies."""
        self._backtest = kwargs.get("backtest", False)
        self._backtest_id = kwargs.get("backtest_id")
        self._portfolio = kwargs.get("portfolio")
        self._commands_queue = kwargs.get("commands_queue")
        self._events_queue = kwargs.get("events_queue")

        if self._commands_queue is None:
            raise ValueError("Commands queue is required")

        if self._events_queue is None:
            raise ValueError("Events queue is required")

        if self._backtest and self._backtest_id is None:
            raise ValueError("Backtest ID is required")

        if not self._backtest:
            sandbox = None

            self._gateway = GatewayService(
                gateway=self._gateway_name,
                backtest=self._backtest,
                sandbox=sandbox,
            )
        else:
            self._gateway = GatewayService(
                gateway=self._gateway_name,
                sandbox=False,
            )

        enabled_strategies = [s for s in self._strategies if s.enabled]

        for strategy in self._strategies:
            if not strategy.enabled:
                self._log.warning(f"Strategy {strategy.name} is not enabled")

        self._strategies = enabled_strategies

        for strategy in self._strategies:
            strategy.setup(
                **kwargs,
            )

        self._analytic = AnalyticComponent(
            asset_id=self._symbol,
            allocation=self._allocation,
            strategies=self._strategies,
            backtest=self._backtest,
            backtest_id=self._backtest_id,
        )

    def start_historical_filling(self) -> None:
        """Mark the asset as currently processing historical data."""
        self._is_historical_filling = True

    def stop_historical_filling(self) -> None:
        """Mark the asset as no longer processing historical data."""
        self._is_historical_filling = False
