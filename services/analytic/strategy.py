"""Strategy-level analytics service (Leaf in Composite pattern)."""

from __future__ import annotations

import datetime
from multiprocessing import Queue
from typing import Any, Dict, List, Optional, Tuple

from enums.command import Command
from enums.quality_method import QualityMethod
from enums.snapshot_event import SnapshotEvent
from interfaces.analytic import AnalyticInterface
from interfaces.orderbook import OrderbookInterface
from models.backtest_expectation import BacktestExpectationModel
from models.order import OrderModel
from models.snapshot import SnapshotModel
from models.tick import TickModel
from providers.horizon_router import HorizonRouterProvider
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


class StrategyAnalytic(AnalyticInterface):
    """Analytics service for strategy-level metrics calculation.

    This is the Leaf component in the Composite pattern. It calculates
    all financial metrics directly from the orderbook and tracks
    individual strategy performance.

    Attributes:
        _strategy_id: Identifier of the strategy being analyzed.
        _orderbook: Service for managing orders and portfolio state.
        _backtest: Whether running in backtest mode.
        _backtest_id: Optional backtest identifier.
        _quality_method: Method for calculating quality score.
        _backtest_expectation: Expected metric ranges for quality calculation.
        _snapshot: Current analytics snapshot.
        _started: Whether analytics tracking has started.
        _started_at: Timestamp when tracking started.
        _ended_at: Timestamp when tracking ended.
        _tick: Current market tick.
        _closed_orders: Count of closed orders.
        _trade_durations: List of trade durations in minutes.
    """

    _asset_id: Optional[str]
    _backtest: bool
    _backtest_expectation: Optional[BacktestExpectationModel]
    _backtest_id: Optional[str]
    _closed_orders: int
    _commands_queue: Optional[Queue[Any]]
    _ended_at: datetime.datetime
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
        orderbook: OrderbookInterface,
        backtest: bool = False,
        backtest_id: Optional[str] = None,
        quality_method: QualityMethod = QualityMethod.FQS,
        backtest_expectation: Optional[BacktestExpectationModel] = None,
        commands_queue: Optional[Queue[Any]] = None,
        asset_id: Optional[str] = None,
    ) -> None:
        """Initialize the strategy analytics service.

        Args:
            strategy_id: Identifier of the strategy being analyzed.
            orderbook: Service for managing orders and portfolio state.
            backtest: Whether running in backtest mode.
            backtest_id: Backtest identifier (required if backtest is True).
            quality_method: Method for calculating quality score.
            backtest_expectation: Expected metric ranges for quality calculation.
            commands_queue: Queue for sending commands to external services.
            asset_id: Identifier of the asset this strategy trades.

        Raises:
            ValueError: If strategy_id is empty.
            ValueError: If backtest is True but backtest_id is None.
        """
        self._log = LoggingService()

        if not strategy_id:
            raise ValueError("Strategy ID is required")

        if backtest and backtest_id is None:
            raise ValueError("Backtest ID is required when backtest is True")

        self._strategy_id = strategy_id
        self._orderbook = orderbook
        self._backtest = backtest
        self._backtest_id = backtest_id
        self._quality_method = quality_method
        self._backtest_expectation = backtest_expectation
        self._commands_queue = commands_queue
        self._asset_id = asset_id

        self._started = False
        self._tick = None
        self._closed_orders = 0
        self._trade_durations = []

        self._snapshot = SnapshotModel(
            backtest=self._backtest,
            backtest_id=self._backtest_id,
            strategy_id=self._strategy_id,
            asset_id=self._asset_id,
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
            quality=0,
        )

    def on_end(self) -> Optional[Dict[str, Any]]:
        """Finalize analytics and generate the strategy report.

        Returns:
            Dictionary containing complete analytics report with all metrics.
        """
        if self._tick is None:
            self._log.error("Tick must be set before ending analytics.")
            return None

        self._ended_at = self._tick.date
        self._perform_calculations()

        days_elapsed = (self._ended_at - self._started_at).days
        quality_score, quality_method_name = self._calculate_quality()
        self._snapshot.quality = quality_score

        report: Dict[str, Any] = {
            **self._snapshot.to_dict(),
            "started_at": str(self._started_at),
            "ended_at": str(self._ended_at),
            "days_elapsed": days_elapsed,
            "num_trades": self._closed_orders,
            "quality": quality_score,
            "quality_method": quality_method_name,
        }

        self._log.info(f"[ANALYTIC_REPORT] Strategy: {self._strategy_id}")
        self._log.info(f"[ANALYTIC_REPORT] {report}")

        return report

    def on_new_day(self) -> None:
        """Handle a new day event. Records history, recalculates metrics and sends snapshot."""
        self._snapshot.performance_history.append(self._snapshot.performance)
        self._snapshot.nav_history.append(self._snapshot.nav)
        self._perform_calculations()

        if not self._backtest or self._commands_queue is None:
            return

        self._snapshot.event = SnapshotEvent.ON_NEW_DAY
        snapshot_data = self._snapshot.to_dict()

        provider = HorizonRouterProvider()
        self._commands_queue.put(
            {
                "command": Command.EXECUTE,
                "function": provider.snapshot_create,
                "args": {"data": snapshot_data},
            }
        )

    def on_new_hour(self) -> None:
        """Handle a new hour event."""
        pass

    def on_new_month(self) -> None:
        """Handle a new month event. Logs monthly performance in live mode."""
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
        """Handle a new market tick. Refreshes snapshot from orderbook.

        Args:
            tick: The current market tick data.
        """
        self._tick = tick
        self._refresh()

        if not self._started:
            self._started = True
            self._started_at = self._tick.date

    def on_transaction(self, order: OrderModel) -> None:
        """Handle a transaction event. Tracks closed orders and profits.

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

    def _calculate_quality(self) -> Tuple[float, str]:
        """Calculate quality score using configured method.

        Returns:
            Tuple of (quality_score, quality_method_name).
        """
        days_elapsed = self._elapsed_days

        return get_quality(
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

    def _is_running_in_live_mode(self) -> bool:
        """Check if running in live (non-simulated) mode."""
        return self._tick is not None and not self._tick.is_simulated

    def _perform_calculations(self) -> None:
        """Calculate all financial metrics and update snapshot."""
        snapshot = self._snapshot
        allocation = snapshot.allocation
        nav = snapshot.nav
        elapsed_days = self._elapsed_days
        performance_history = snapshot.performance_history
        nav_history = snapshot.nav_history
        profit_history = snapshot.profit_history
        max_drawdown = snapshot.max_drawdown

        snapshot.r2 = get_r2(performance_history)
        snapshot.cagr = get_cagr(allocation, nav, elapsed_days)
        snapshot.calmar_ratio = get_calmar_ratio(snapshot.cagr, max_drawdown)
        snapshot.expected_shortfall = get_expected_shortfall(nav_history)
        snapshot.profit_factor = get_profit_factor(profit_history)
        snapshot.recovery_factor = get_recovery_factor(snapshot.performance_percentage, max_drawdown)
        snapshot.sharpe_ratio = get_sharpe_ratio(nav_history)
        snapshot.sortino_ratio = get_sortino_ratio(nav_history)
        snapshot.ulcer_index = get_ulcer_index(nav_history)
        snapshot.win_ratio = get_win_ratio(profit_history)
        snapshot.average_trade_duration = get_average_trade_duration(self._trade_durations)

    def _refresh(self) -> None:
        """Refresh snapshot data from orderbook."""
        self._snapshot.nav = self._orderbook.nav
        self._snapshot.allocation = self._orderbook.allocation
        self._snapshot.nav_peak = max(self._snapshot.nav_peak, self._snapshot.nav)

        if self._snapshot.drawdown < 0:
            self._snapshot.max_drawdown = min(
                self._snapshot.max_drawdown,
                self._snapshot.drawdown,
            )

    @property
    def _elapsed_days(self) -> int:
        """Calculate number of days elapsed since tracking started."""
        if self._tick is None:
            return 0
        return (self._tick.date - self._started_at).days

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
