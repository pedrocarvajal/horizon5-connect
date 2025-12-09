"""Service for calculating and tracking financial analytics during backtests."""

from __future__ import annotations

import datetime
from multiprocessing import Queue
from typing import Any, Dict, List, Optional

from enums.quality_method import QualityMethod
from interfaces.analytic import AnalyticInterface
from interfaces.orderbook import OrderbookInterface
from models.backtest_expectation import BacktestExpectationModel
from models.order import OrderModel
from models.snapshot import SnapshotModel
from models.tick import TickModel
from services.analytic.helpers.get_average_trade_duration import get_average_trade_duration
from services.analytic.helpers.get_cagr import get_cagr
from services.analytic.helpers.get_calmar_ratio import get_calmar_ratio
from services.analytic.helpers.get_expected_shortfall import get_expected_shortfall
from services.analytic.helpers.get_profit_factor import get_profit_factor
from services.analytic.helpers.get_quality import get_quality
from services.analytic.helpers.get_r2 import get_r2
from services.analytic.helpers.get_recovery_factor import get_recovery_factor
from services.analytic.helpers.get_sharpe_ratio import get_sharpe_ratio
from services.analytic.helpers.get_sortino_ratio import get_sortino_ratio
from services.analytic.helpers.get_ulcer_index import get_ulcer_index
from services.analytic.helpers.get_win_ratio import get_win_ratio
from services.logging import LoggingService


class AnalyticService(AnalyticInterface):
    """
    Service for calculating and tracking financial analytics during backtests.

    This service monitors trading performance, calculates various financial
    metrics (Sharpe ratio, Sortino ratio, CAGR, etc.), and stores snapshots
    of analytics data at different events (start, daily, end). It integrates
    with the Horizon Router API to persist analytics data.

    Attributes:
        _backtest: Whether the service is running in backtest mode.
        _backtest_id: Optional backtest identifier.
        _strategy_id: Identifier of the strategy being analyzed.
        _orderbook: Service for managing orders and portfolio state.
        _commands_queue: Queue for sending commands to external services.
        _events_queue: Queue for receiving events from external services.
        _log: Logging service instance for logging operations.
        _started: Whether analytics tracking has started.
        _started_at: Timestamp when analytics tracking started.
        _ended_at: Timestamp when analytics tracking ended.
        _tick: Current market tick data.
        _snapshot: Current analytics snapshot model.
        _closed_orders: Count of closed orders.
    """

    _backtest: bool
    _backtest_expectation: Optional[BacktestExpectationModel]
    _backtest_id: Optional[str]
    _closed_orders: int
    _commands_queue: Queue[Any]
    _ended_at: datetime.datetime
    _events_queue: Queue[Any]
    _orderbook: OrderbookInterface
    _quality_method: QualityMethod
    _snapshot: SnapshotModel
    _started: bool
    _started_at: datetime.datetime
    _strategy_id: str
    _tick: Optional[TickModel]
    _trade_durations: List[float]

    _log: LoggingService

    def __init__(
        self,
        strategy_id: str,
        backtest: bool,
        backtest_id: Optional[str],
        orderbook: OrderbookInterface,
        commands_queue: Queue[Any],
        events_queue: Queue[Any],
        quality_method: QualityMethod = QualityMethod.FQS,
        backtest_expectation: Optional[BacktestExpectationModel] = None,
    ) -> None:
        """
        Initialize the analytics service.

        Args:
            strategy_id: Identifier of the strategy being analyzed.
            backtest: Whether the service is running in backtest mode.
            backtest_id: Optional backtest identifier. Required if backtest is True.
            orderbook: Service for managing orders and portfolio state.
            commands_queue: Queue for sending commands to external services.
            events_queue: Queue for receiving events from external services.
            quality_method: Method for calculating quality score.
            backtest_expectation: BacktestExpectationModel with [min, expected] ranges.

        Raises:
            ValueError: If backtest is True but backtest_id is None.
            ValueError: If strategy_id is None or empty.
        """
        self._log = LoggingService()

        self._backtest = backtest
        self._backtest_id = backtest_id
        self._strategy_id = strategy_id
        self._orderbook = orderbook
        self._commands_queue = commands_queue
        self._events_queue = events_queue
        self._quality_method = quality_method
        self._backtest_expectation = backtest_expectation

        if self._backtest and self._backtest_id is None:
            raise ValueError("Backtest ID is required when backtest is True")

        if not self._strategy_id:
            raise ValueError("Strategy ID is required")

        self._started = False
        self._tick = None
        self._closed_orders = 0
        self._trade_durations = []

        self._snapshot = SnapshotModel(
            backtest=self._backtest,
            backtest_id=self._backtest_id,
            strategy_id=self._strategy_id,
            nav=self._orderbook.nav,
            allocation=self._orderbook.allocation,
            nav_peak=self._orderbook.nav,
            r2=0,
            cagr=0,
            calmar_ratio=0,
            expected_shortfall=0,
            max_drawdown=0,
            profit_factor=0,
            recovery_factor=0,
            sharpe_ratio=0,
            sortino_ratio=0,
            ulcer_index=0,
            win_ratio=0,
            average_trade_duration=0,
        )

    def on_end(self) -> Optional[Dict[str, Any]]:
        """
        Handle the end of analytics tracking.

        Records the end timestamp, performs final calculations, stores the
        final snapshot, updates the backtest status to completed, and generates
        the final report.

        Returns:
            Dictionary containing the analytics report, or None if tick is not set.
        """
        if self._tick is None:
            self._log.error("Tick must be set before ending analytics.")
            return None

        self._ended_at = self._tick.date
        self._perform_calculations()
        return self._report()

    def on_new_day(self) -> None:
        """
        Handle a new day event.

        Records the current performance and NAV in history, performs all
        financial calculations, and stores a daily snapshot.
        """
        self._snapshot.performance_history.append(self._snapshot.performance)
        self._snapshot.nav_history.append(self._snapshot.nav)
        self._perform_calculations()

    def on_new_month(self) -> None:
        """
        Handle a new month event.

        Logs monthly performance metrics if running in live (non-simulated) mode.
        Performance and drawdown percentages are displayed.
        """
        performance = self._snapshot.performance
        performance_percentage = self._snapshot.performance_percentage * 100
        max_drawdown_percentage = self._snapshot.max_drawdown * 100

        if self._is_running_in_live_mode():
            message = (
                f"Closing month, with: {performance:.2f} ({performance_percentage:.2f}%), "
                f"max drawdown: {max_drawdown_percentage:.2f}%."
            )
            self._log.info(message)

    def on_tick(self, tick: TickModel) -> None:
        """
        Handle a new market tick event.

        Updates the current tick, refreshes snapshot data, and if this is the
        first tick, initializes the analytics tracking and stores the start snapshot.

        Args:
            tick: The current market tick data.
        """
        self._tick = tick
        self._refresh()

        if not self._started:
            self._started = True
            self._started_at = self._tick.date

    def on_transaction(self, order: OrderModel) -> None:
        """
        Handle a transaction event (order status change).

        When an order is closed, this method updates the executed orders count,
        records the profit in the snapshot's profit history, calculates trade
        duration, and stores the order via the commands queue.

        Args:
            order: The order model representing the transaction.
        """
        if order.status.is_closed():
            self._closed_orders += 1
            self._snapshot.profit_history.append(order.profit)

            if order.created_at is not None and order.updated_at is not None:
                duration_seconds = (order.updated_at - order.created_at).total_seconds()
                duration_minutes = duration_seconds / 60
                self._trade_durations.append(duration_minutes)

    def _is_running_in_live_mode(self) -> bool:
        """
        Check if the service is running in live (non-simulated) mode.

        Returns:
            True if tick exists and is not simulated, False otherwise.
        """
        return self._tick is not None and not self._tick.is_simulated

    def _perform_calculations(self) -> None:
        """
        Calculate all financial metrics and update the snapshot.

        Computes various risk-adjusted return metrics including R², CAGR,
        Calmar ratio, expected shortfall, profit factor, recovery factor,
        Sharpe ratio, Sortino ratio, ulcer index, win ratio, and average
        trade duration.
        """
        allocation = self._snapshot.allocation
        nav = self._snapshot.nav
        elapsed_days = self._elapsed_days
        performance = self._snapshot.performance_percentage
        performance_history = self._snapshot.performance_history
        nav_history = self._snapshot.nav_history
        profit_history = self._snapshot.profit_history
        max_drawdown = self._snapshot.max_drawdown

        self._snapshot.r2 = get_r2(performance_history)
        self._snapshot.cagr = get_cagr(allocation, nav, elapsed_days)
        self._snapshot.calmar_ratio = get_calmar_ratio(self._snapshot.cagr, max_drawdown)
        self._snapshot.expected_shortfall = get_expected_shortfall(nav_history)
        self._snapshot.profit_factor = get_profit_factor(profit_history)
        self._snapshot.recovery_factor = get_recovery_factor(performance, max_drawdown)
        self._snapshot.sharpe_ratio = get_sharpe_ratio(nav_history)
        self._snapshot.sortino_ratio = get_sortino_ratio(nav_history)
        self._snapshot.ulcer_index = get_ulcer_index(nav_history)
        self._snapshot.win_ratio = get_win_ratio(profit_history)
        self._snapshot.average_trade_duration = get_average_trade_duration(self._trade_durations)

    def _refresh(self) -> None:
        """
        Refresh snapshot data from the orderbook.

        Updates NAV, allocation, NAV peak, and max drawdown based on current
        orderbook state.
        """
        self._snapshot.nav = self._orderbook.nav
        self._snapshot.allocation = self._orderbook.allocation
        self._snapshot.nav_peak = max(self._snapshot.nav_peak, self._snapshot.nav)

        if self._snapshot.drawdown < 0:
            self._snapshot.max_drawdown = min(
                self._snapshot.max_drawdown,
                self._snapshot.drawdown,
            )

    def _report(self) -> Dict[str, Any]:
        """
        Generate and log the final analytics report.

        Logs backtest ID and strategy ID, then outputs a detailed JSON report
        containing all snapshot metrics, timestamps, and elapsed days.

        Returns:
            Dictionary containing the complete analytics report.
        """
        self._log.info(f"Backtest ID: {self._backtest_id}")
        self._log.info(f"Strategy: {self._strategy_id}")

        days_elapsed = (self._ended_at - self._started_at).days

        quality, quality_method = get_quality(
            method=self._quality_method,
            expectations=self._backtest_expectation,
            days_elapsed=days_elapsed,
            r_squared=self._snapshot.r2,
            max_drawdown=self._snapshot.max_drawdown,
            profit_factor=self._snapshot.profit_factor,
            num_trades=self._closed_orders,
            recovery_factor=self._snapshot.recovery_factor,
            win_ratio=self._snapshot.win_ratio,
            trade_duration=self._snapshot.average_trade_duration,
            performance_percentage=self._snapshot.performance_percentage,
        )

        report: Dict[str, Any] = {
            **self._snapshot.to_dict(),
            "started_at": str(self._started_at),
            "ended_at": str(self._ended_at),
            "days_elapsed": days_elapsed,
            "num_trades": self._closed_orders,
            "quality": quality,
            "quality_method": quality_method,
        }

        self._log.info(f"[ANALYTIC_REPORT] Strategy: {self._strategy_id}")
        self._log.info(f"[ANALYTIC_REPORT] {report}")

        return report

    @property
    def _elapsed_days(self) -> int:
        """
        Calculate the number of days elapsed since tracking started.

        Returns:
            Number of days elapsed, or 0 if tick is not yet available.
        """
        if self._tick is None:
            return 0
        return (self._tick.date - self._started_at).days

    @property
    def snapshot(self) -> SnapshotModel:
        """Return the current snapshot."""
        return self._snapshot
