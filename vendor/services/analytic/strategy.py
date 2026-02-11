"""Strategy-level analytics service (Leaf in Composite pattern)."""

from __future__ import annotations

import datetime
from multiprocessing import Queue
from typing import Any, Dict, List, Optional, Tuple

from vendor.enums.quality_method import QualityMethod
from vendor.enums.quality_vs_benchmark_method import QualityVsBenchmarkMethod
from vendor.enums.snapshot_event import SnapshotEvent
from vendor.interfaces.orderbook import OrderbookInterface
from vendor.models.backtest_expectation import BacktestExpectationModel
from vendor.models.order import OrderModel
from vendor.models.snapshot import SnapshotModel
from vendor.services.analytic.helpers.get_average_trade_duration import get_average_trade_duration
from vendor.services.analytic.helpers.get_max_trade_duration import get_max_trade_duration
from vendor.services.analytic.helpers.get_overnight_metrics import get_overnight_metrics
from vendor.services.analytic.helpers.get_profit_factor import get_profit_factor
from vendor.services.analytic.helpers.get_propfirm_metrics import get_propfirm_metrics
from vendor.services.analytic.helpers.get_quality import get_quality
from vendor.services.analytic.helpers.get_quality_propfirm import get_quality_propfirm
from vendor.services.analytic.helpers.get_quality_vs_benchmark import get_quality_vs_benchmark
from vendor.services.analytic.helpers.get_win_ratio import get_win_ratio
from vendor.services.analytic.wrappers.analytic import AnalyticWrapper
from vendor.services.logging import LoggingService


class StrategyAnalytic(AnalyticWrapper):
    """Analytics service for strategy-level metrics calculation.

    This is the Leaf component in the Composite pattern. It calculates
    all financial metrics directly from the orderbook and tracks
    individual strategy performance.

    Attributes:
        _strategy_id: Identifier of the strategy being analyzed.
        _orderbook: Service for managing orders and portfolio state.
        _quality_method: Method for calculating quality score.
        _backtest_expectation: Expected metric ranges for quality calculation.
        _ended_at: Timestamp when tracking ended.
        _closed_orders: Count of closed orders.
        _trade_durations: List of trade durations in minutes.
    """

    _asset_id: Optional[str]
    _backtest_expectation: Optional[BacktestExpectationModel]
    _closed_orders: int
    _ended_at: datetime.datetime
    _orderbook: OrderbookInterface
    _portfolio_id: Optional[str]
    _quality_method: QualityMethod
    _strategy_id: str
    _trade_durations: List[float]
    _trade_timestamps: List[Tuple[datetime.datetime, datetime.datetime]]
    _current_day_profit: float

    def __init__(
        self,
        strategy_id: str,
        orderbook: OrderbookInterface,
        backtest_id: Optional[str] = None,
        quality_method: QualityMethod = QualityMethod.FQS,
        quality_vs_benchmark_method: QualityVsBenchmarkMethod = QualityVsBenchmarkMethod.FQS_BENCHMARK,
        backtest_expectation: Optional[BacktestExpectationModel] = None,
        commands_queue: Optional[Queue[Any]] = None,
        asset_id: Optional[str] = None,
        portfolio_id: Optional[str] = None,
    ) -> None:
        """Initialize the strategy analytics service.

        Args:
            strategy_id: Identifier of the strategy being analyzed.
            orderbook: Service for managing orders and portfolio state.
            backtest_id: Backtest identifier (None for live mode).
            quality_method: Method for calculating quality score.
            quality_vs_benchmark_method: Method for calculating quality vs benchmark score.
            backtest_expectation: Expected metric ranges for quality calculation.
            commands_queue: Queue for sending commands to external services.
            asset_id: Identifier of the asset this strategy trades.
            portfolio_id: Identifier of the parent portfolio.

        Raises:
            ValueError: If strategy_id is empty.
        """
        self._log = LoggingService()

        if not strategy_id:
            raise ValueError("Strategy ID is required")

        self._strategy_id = strategy_id
        self._orderbook = orderbook
        self._backtest_id = backtest_id
        self._quality_method = quality_method
        self._quality_vs_benchmark_method = quality_vs_benchmark_method
        self._backtest_expectation = backtest_expectation
        self._commands_queue = commands_queue
        self._asset_id = asset_id
        self._portfolio_id = portfolio_id

        self._started = False
        self._started_at = None
        self._tick = None
        self._closed_orders = 0
        self._buy_orders = 0
        self._sell_orders = 0
        self._trade_durations = []
        self._trade_timestamps = []
        self._current_day_profit = 0.0
        self._previous_day_nav = self._orderbook.nav
        self._month_start_nav = self._orderbook.nav

        self._snapshot = SnapshotModel(
            strategy_id=self._strategy_id,
            portfolio_id=self._portfolio_id,
            asset_id=self._asset_id,
            backtest_id=self._backtest_id,
            is_backtest=self._backtest_id is not None,
            capital_allocation=self._orderbook.allocation,
            capital_nav=self._orderbook.nav,
            capital_nav_peak=self._orderbook.nav,
            capital_balance=self._orderbook.allocation,
            capital_balance_peak=self._orderbook.allocation,
        )

    def on_end(self) -> Optional[Dict[str, Any]]:
        """Finalize analytics and generate the strategy report.

        Returns:
            Dictionary containing complete analytics report with all metrics.
        """
        if not self._tick:
            return None

        if not self._started_at:
            return None

        self._ended_at = self._tick.date
        self._perform_calculations()

        days_elapsed = (self._ended_at - self._started_at).days
        quality_score, _ = self._calculate_quality()
        quality_vs_benchmark_score = self._calculate_quality_vs_benchmark()
        self._snapshot.score_quality = quality_score
        self._snapshot.score_quality_vs_benchmark = quality_vs_benchmark_score
        self._snapshot.time_days_elapsed = days_elapsed
        self._snapshot.event = SnapshotEvent.BACKTEST_END

        nav_change = self._snapshot.capital_nav - self._previous_day_nav
        realized_profit = self._current_day_profit
        last_day_profit = nav_change if abs(nav_change) >= abs(realized_profit) else realized_profit

        if last_day_profit != 0.0:
            self._snapshot.history_daily_profit.append(last_day_profit)

        self._calculate_propfirm_metrics()

        snapshot_data = {
            "strategy_id": self._snapshot.strategy_id,
            "portfolio_id": self._snapshot.portfolio_id,
            "asset_id": self._snapshot.asset_id,
            "backtest_id": self._snapshot.backtest_id,
            "backtest": self._snapshot.is_backtest,
            "event": self._snapshot.event.value,
            "data": self._snapshot.to_dict(),
            "created_at": int(self._tick.date.timestamp()),
        }

        self._send_snapshot_to_queue(snapshot_data)

        report: Dict[str, Any] = {
            "strategy_id": self._strategy_id,
            **self._snapshot.to_dict(),
        }

        return report

    def on_new_month(self) -> None:
        """Handle a new month event. Logs monthly performance in live mode."""
        super().on_new_month()

        if self._is_running_in_live_mode():
            monthly_performance = self._snapshot.performance_monthly
            monthly_percentage = self._snapshot.performance_monthly_percentage * 100
            max_drawdown_percentage = self._snapshot.performance_max_drawdown * 100

            message = (
                f"Closing month, with: {monthly_performance:.2f} ({monthly_percentage:.2f}%), "
                f"max drawdown: {max_drawdown_percentage:.2f}%."
            )
            self._log.info(message)

    def on_new_day(self) -> None:
        """Handle a new day event. Extends base to track daily profits for prop firm metrics."""
        self._refresh()

        nav_change = self._snapshot.capital_nav - self._previous_day_nav
        realized_profit = self._current_day_profit
        daily_profit = nav_change if abs(nav_change) >= abs(realized_profit) else realized_profit

        self._snapshot.history_daily_profit.append(daily_profit)
        self._current_day_profit = 0.0

        super().on_new_day()

    def on_transaction(self, order: OrderModel) -> None:
        """Handle a transaction event. Tracks closed orders and profits.

        Args:
            order: The order model representing the transaction.
        """
        if order.status.is_closed():
            self._closed_orders += 1
            self._snapshot.history_profit.append(order.profit)
            self._snapshot.capital_balance += order.profit
            self._snapshot.capital_balance_peak = max(
                self._snapshot.capital_balance_peak,
                self._snapshot.capital_balance,
            )

            self._snapshot.history_balance.append(self._snapshot.capital_balance)
            self._current_day_profit += order.profit

            if order.side is not None:
                if order.side.is_buy():
                    self._buy_orders += 1

                elif order.side.is_sell():
                    self._sell_orders += 1

            if order.created_at is not None and order.updated_at is not None:
                duration_seconds = (order.updated_at - order.created_at).total_seconds()
                duration_minutes = duration_seconds / 60
                self._trade_durations.append(duration_minutes)
                self._trade_timestamps.append((order.created_at, order.updated_at))

        if order.status.is_closed() or order.status.is_cancelled():
            self._send_order_to_backend(order)

    def _calculate_quality(self) -> Tuple[float, str]:
        """Calculate quality score using configured method.

        Returns:
            Tuple of (quality_score, quality_method_name).
        """
        days_elapsed = self._get_elapsed_days()

        return get_quality(
            method=self._quality_method,
            expectations=self._backtest_expectation or BacktestExpectationModel.default(),
            days_elapsed=days_elapsed,
            r_squared=self._snapshot.performance_r_squared,
            max_drawdown=self._snapshot.performance_max_drawdown,
            profit_factor=self._snapshot.trade_profit_factor,
            num_trades=self._closed_orders,
            recovery_factor=self._snapshot.performance_recovery_factor,
            win_ratio=self._snapshot.trade_win_ratio,
            trade_duration=self._snapshot.trade_average_duration,
            performance_percentage=self._snapshot.performance_percentage,
        )

    def _calculate_quality_vs_benchmark(self) -> float:
        """Calculate quality score comparing strategy performance against benchmark.

        Returns:
            Quality score between 0 and 1.
        """
        return get_quality_vs_benchmark(
            method=self._quality_vs_benchmark_method,
            alpha=self._snapshot.benchmark_alpha,
            information_ratio=self._snapshot.benchmark_information_ratio,
            strategy_nav_history=self._snapshot.history_nav,
            benchmark_price_history=self._snapshot.history_benchmark_price,
            benchmark_initial_price=self._snapshot.benchmark_initial_price,
        )

    def _is_running_in_live_mode(self) -> bool:
        """Check if running in live (non-simulated) mode."""
        return self._tick is not None and not self._tick.is_simulated

    def _perform_calculations(self) -> None:
        """Calculate all financial metrics and update snapshot."""
        self._perform_base_calculations()

        snapshot = self._snapshot
        profit_history = snapshot.history_profit

        snapshot.trade_profit_factor = get_profit_factor(profit_history)
        snapshot.trade_win_ratio = get_win_ratio(profit_history)
        snapshot.trade_total_orders = self._closed_orders
        snapshot.trade_buy_orders = self._buy_orders
        snapshot.trade_sell_orders = self._sell_orders
        snapshot.trade_average_duration = get_average_trade_duration(self._trade_durations)
        snapshot.trade_max_duration = get_max_trade_duration(self._trade_durations)

        overnight_count, overnight_ratio = get_overnight_metrics(self._trade_timestamps)
        snapshot.trade_overnight_count = overnight_count
        snapshot.trade_overnight_ratio = overnight_ratio

    def _refresh(self) -> None:
        """Refresh snapshot data from orderbook."""
        self._snapshot.capital_nav = self._orderbook.nav
        self._snapshot.capital_allocation = self._orderbook.allocation
        self._snapshot.capital_nav_peak = max(self._snapshot.capital_nav_peak, self._snapshot.capital_nav)
        self._update_max_drawdown()

    def _send_order_to_backend(self, order: OrderModel) -> None:
        """Send order data to backend via command queue.

        Args:
            order: The order model to send.
        """
        pass

    def _calculate_propfirm_metrics(self) -> None:
        """Calculate prop firm compliance metrics and quality score."""
        snapshot = self._snapshot
        daily_profits = snapshot.history_daily_profit
        initial_balance = snapshot.capital_allocation
        max_drawdown = snapshot.performance_max_drawdown

        propfirm = get_propfirm_metrics(daily_profits, initial_balance, max_drawdown)

        snapshot.propfirm_best_day_profit = propfirm.best_day_profit
        snapshot.propfirm_best_day_profit_ratio = propfirm.best_day_profit_ratio
        snapshot.propfirm_trading_days = propfirm.trading_days
        snapshot.propfirm_daily_loss_compliant = propfirm.daily_loss_compliant
        snapshot.propfirm_overall_loss_compliant = propfirm.overall_loss_compliant
        snapshot.propfirm_consistency_compliant = propfirm.consistency_compliant
        snapshot.propfirm_trading_days_compliant = propfirm.trading_days_compliant

        snapshot.risk_max_daily_loss = propfirm.max_daily_loss
        snapshot.risk_max_daily_profit = propfirm.max_daily_profit
        snapshot.risk_daily_loss_breach_count = propfirm.daily_loss_breach_count

        snapshot.score_quality_propfirm = get_quality_propfirm(
            consistency_ratio=propfirm.best_day_profit_ratio,
            max_daily_loss=propfirm.max_daily_loss,
            max_drawdown=max_drawdown,
            profit_factor=snapshot.trade_profit_factor,
            trading_days=propfirm.trading_days,
        )
