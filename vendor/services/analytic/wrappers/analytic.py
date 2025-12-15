"""Base analytics wrapper with common implementation for all analytic services."""

from __future__ import annotations

import datetime
from abc import abstractmethod
from multiprocessing import Queue
from typing import Any, List, Optional

from vendor.enums.command import Command
from vendor.enums.snapshot_event import SnapshotEvent
from vendor.interfaces.analytic import AnalyticInterface
from vendor.models.snapshot import SnapshotModel
from vendor.models.tick import TickModel
from vendor.providers.horizon_router import HorizonRouterProvider
from vendor.services.analytic.helpers.get_alpha import get_alpha
from vendor.services.analytic.helpers.get_beta import get_beta
from vendor.services.analytic.helpers.get_cagr import get_cagr
from vendor.services.analytic.helpers.get_calmar_ratio import get_calmar_ratio
from vendor.services.analytic.helpers.get_correlation import get_correlation
from vendor.services.analytic.helpers.get_expected_shortfall import get_expected_shortfall
from vendor.services.analytic.helpers.get_information_ratio import get_information_ratio
from vendor.services.analytic.helpers.get_r2 import get_r2
from vendor.services.analytic.helpers.get_recovery_factor import get_recovery_factor
from vendor.services.analytic.helpers.get_sharpe_ratio import get_sharpe_ratio
from vendor.services.analytic.helpers.get_sortino_ratio import get_sortino_ratio
from vendor.services.analytic.helpers.get_tracking_error import get_tracking_error
from vendor.services.analytic.helpers.get_ulcer_index import get_ulcer_index
from vendor.services.logging import LoggingService

MIN_OBSERVATIONS_FOR_BENCHMARK = 2


class AnalyticWrapper(AnalyticInterface):
    """Base wrapper class providing common analytics functionality.

    This abstract class implements the Template Method pattern for analytics services.
    Subclasses must implement _refresh() and _perform_aggregated_calculations() methods
    to define their specific data source behavior.

    Attributes:
        _backtest: Whether running in backtest mode.
        _backtest_id: Optional backtest identifier.
        _commands_queue: Queue for sending commands to external services.
        _snapshot: Current analytics snapshot.
        _started: Whether analytics tracking has started.
        _started_at: Timestamp when tracking started.
        _tick: Current market tick.
        _previous_day_nav: NAV from the previous day for daily performance calculation.
    """

    _backtest: bool
    _backtest_id: Optional[str]
    _commands_queue: Optional[Queue[Any]]
    _previous_day_nav: float
    _snapshot: SnapshotModel
    _started: bool
    _started_at: Optional[datetime.datetime]
    _tick: Optional[TickModel]

    _log: LoggingService

    def on_new_day(self) -> None:
        """Handle a new day event. Template method for daily processing.

        Calls _refresh() to update data, records history, performs calculations,
        and sends snapshot to backend.
        """
        self._refresh()
        self._snapshot.performance_history.append(self._snapshot.performance)
        self._snapshot.nav_history.append(self._snapshot.nav)
        self._perform_calculations()
        self._calculate_daily_performance()

        if not self._tick:
            return

        self._snapshot.benchmark_price_history.append(self._tick.close_price)
        self._snapshot.event = SnapshotEvent.ON_NEW_DAY
        snapshot_data = self._snapshot.to_dict()
        snapshot_data["created_at"] = int(self._tick.date.timestamp())

        self._send_snapshot_to_queue(snapshot_data)
        self._previous_day_nav = self._snapshot.nav

    def on_new_hour(self) -> None:
        """Handle a new hour event."""
        pass

    def on_tick(self, tick: TickModel) -> None:
        """Handle a new market tick. Refreshes snapshot data.

        Args:
            tick: The current market tick data.
        """
        self._tick = tick
        self._refresh()

        if not self._started:
            self._started = True
            self._started_at = self._tick.date
            self._snapshot.benchmark_initial_price = tick.close_price
            self._snapshot.benchmark_current_price = tick.close_price
        else:
            self._snapshot.benchmark_current_price = tick.close_price

    def _calculate_daily_performance(self) -> None:
        """Calculate daily performance metrics and update snapshot."""
        current_nav = self._snapshot.nav
        previous_nav = self._previous_day_nav

        if previous_nav > 0:
            self._snapshot.daily_performance = current_nav - previous_nav
            self._snapshot.daily_performance_percentage = (current_nav - previous_nav) / previous_nav
        else:
            self._snapshot.daily_performance = 0.0
            self._snapshot.daily_performance_percentage = 0.0

    def _send_snapshot_to_queue(self, snapshot_data: dict[str, Any]) -> None:
        if not self._commands_queue:
            return

        provider = HorizonRouterProvider()
        self._commands_queue.put(
            {
                "command": Command.EXECUTE,
                "function": provider.snapshot_create,
                "args": {"data": snapshot_data},
            }
        )

    def _get_elapsed_days(self) -> int:
        """Calculate number of days elapsed since tracking started.

        Returns:
            Number of days elapsed, or 0 if tracking hasn't started.
        """
        if not self._tick or not self._started_at:
            return 0

        return (self._tick.date - self._started_at).days

    def _perform_base_calculations(self) -> None:
        """Calculate base financial metrics common to all analytics services.

        Updates r2, cagr, calmar_ratio, expected_shortfall, recovery_factor,
        sharpe_ratio, sortino_ratio, and ulcer_index on the snapshot.
        """
        snapshot = self._snapshot
        allocation = snapshot.allocation
        nav = snapshot.nav
        elapsed_days = self._get_elapsed_days()
        performance_history = snapshot.performance_history
        nav_history = snapshot.nav_history
        max_drawdown = snapshot.max_drawdown

        snapshot.r2 = get_r2(performance_history)
        snapshot.cagr = get_cagr(allocation, nav, elapsed_days)
        snapshot.calmar_ratio = get_calmar_ratio(snapshot.cagr, max_drawdown)
        snapshot.expected_shortfall = get_expected_shortfall(nav_history)
        snapshot.recovery_factor = get_recovery_factor(snapshot.performance_percentage, max_drawdown)
        snapshot.sharpe_ratio = get_sharpe_ratio(nav_history)
        snapshot.sortino_ratio = get_sortino_ratio(nav_history)
        snapshot.ulcer_index = get_ulcer_index(nav_history)

        self._perform_benchmark_calculations()

    def _perform_benchmark_calculations(self) -> None:
        """Calculate benchmark comparison metrics.

        Updates alpha, beta, correlation, tracking_error, and information_ratio
        on the snapshot using strategy NAV history vs benchmark price history.
        """
        snapshot = self._snapshot
        nav_history = snapshot.nav_history
        benchmark_price_history = snapshot.benchmark_price_history
        allocation = snapshot.allocation

        min_observations = MIN_OBSERVATIONS_FOR_BENCHMARK

        if len(nav_history) < min_observations or len(benchmark_price_history) < min_observations:
            return

        if snapshot.benchmark_initial_price == 0:
            return

        strategy_returns: List[float] = []
        benchmark_returns: List[float] = []

        previous_nav = allocation
        previous_benchmark_price = snapshot.benchmark_initial_price

        min_length = min(len(nav_history), len(benchmark_price_history))

        for i in range(min_length):
            current_nav = nav_history[i]
            current_benchmark_price = benchmark_price_history[i]

            if previous_nav > 0:
                strategy_return = (current_nav - previous_nav) / previous_nav
                strategy_returns.append(strategy_return)

            if previous_benchmark_price > 0:
                benchmark_return = (current_benchmark_price - previous_benchmark_price) / previous_benchmark_price
                benchmark_returns.append(benchmark_return)

            previous_nav = current_nav
            previous_benchmark_price = current_benchmark_price

        if len(strategy_returns) < min_observations or len(benchmark_returns) < min_observations:
            return

        min_returns_length = min(len(strategy_returns), len(benchmark_returns))
        strategy_returns = strategy_returns[:min_returns_length]
        benchmark_returns = benchmark_returns[:min_returns_length]

        snapshot.beta = get_beta(strategy_returns, benchmark_returns)
        snapshot.correlation = get_correlation(strategy_returns, benchmark_returns)
        snapshot.tracking_error = get_tracking_error(strategy_returns, benchmark_returns)
        snapshot.alpha = get_alpha(strategy_returns, benchmark_returns, snapshot.beta)
        snapshot.information_ratio = get_information_ratio(snapshot.alpha, snapshot.tracking_error)

    @abstractmethod
    def _perform_calculations(self) -> None:
        """Perform all metric calculations.

        Must be implemented by subclasses. Should call _perform_base_calculations()
        and then add any aggregation-specific calculations.
        """
        pass

    @abstractmethod
    def _refresh(self) -> None:
        """Refresh snapshot data from the underlying data source.

        Must be implemented by subclasses to define how NAV and other
        metrics are obtained (from orderbook, strategies, or assets).
        """
        pass

    def _update_max_drawdown(self) -> None:
        """Update max drawdown if current drawdown is lower."""
        if self._snapshot.drawdown < 0:
            self._snapshot.max_drawdown = min(
                self._snapshot.max_drawdown,
                self._snapshot.drawdown,
            )

    @property
    def nav(self) -> float:
        """Return the current net asset value."""
        return self._snapshot.nav

    @property
    def quality(self) -> float:
        """Return the current quality score."""
        return self._snapshot.quality

    @property
    def snapshot(self) -> SnapshotModel:
        """Return the current snapshot."""
        return self._snapshot
