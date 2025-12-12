"""Strategy-level analytics service (Leaf in Composite pattern)."""

from __future__ import annotations

import datetime
from multiprocessing import Queue
from typing import Any, Dict, List, Optional, Tuple

from enums.command import Command
from enums.quality_method import QualityMethod
from interfaces.orderbook import OrderbookInterface
from models.backtest_expectation import BacktestExpectationModel
from models.order import OrderModel
from models.snapshot import SnapshotModel
from providers.horizon_router import HorizonRouterProvider
from services.analytic.helpers.get_average_trade_duration import get_average_trade_duration
from services.analytic.helpers.get_profit_factor import get_profit_factor
from services.analytic.helpers.get_quality import get_quality
from services.analytic.helpers.get_win_ratio import get_win_ratio
from services.analytic.wrappers.analytic import AnalyticWrapper
from services.logging import LoggingService


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
        portfolio_id: Optional[str] = None,
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
            portfolio_id: Identifier of the parent portfolio.

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
        self._portfolio_id = portfolio_id

        self._started = False
        self._started_at = None
        self._tick = None
        self._closed_orders = 0
        self._buy_orders = 0
        self._sell_orders = 0
        self._trade_durations = []
        self._previous_day_nav = self._orderbook.nav

        self._snapshot = SnapshotModel(
            backtest=self._backtest,
            backtest_id=self._backtest_id,
            portfolio_id=self._portfolio_id,
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

        assert self._started_at is not None
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
            "benchmark_initial_price": self._snapshot.benchmark_initial_price,
            "benchmark_final_price": self._snapshot.benchmark_current_price,
        }

        return report

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

    def on_transaction(self, order: OrderModel) -> None:
        """Handle a transaction event. Tracks closed orders and profits.

        Args:
            order: The order model representing the transaction.
        """
        if order.status.is_closed():
            self._closed_orders += 1
            self._snapshot.profit_history.append(order.profit)

            if order.side is not None:
                if order.side.is_buy():
                    self._buy_orders += 1

                elif order.side.is_sell():
                    self._sell_orders += 1

            if order.created_at is not None and order.updated_at is not None:
                duration_seconds = (order.updated_at - order.created_at).total_seconds()
                duration_minutes = duration_seconds / 60
                self._trade_durations.append(duration_minutes)

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
        self._perform_base_calculations()

        snapshot = self._snapshot
        profit_history = snapshot.profit_history

        snapshot.profit_factor = get_profit_factor(profit_history)
        snapshot.win_ratio = get_win_ratio(profit_history)
        snapshot.total_orders = self._closed_orders
        snapshot.total_buy_orders = self._buy_orders
        snapshot.total_sell_orders = self._sell_orders
        snapshot.average_trade_duration = get_average_trade_duration(self._trade_durations)

    def _refresh(self) -> None:
        """Refresh snapshot data from orderbook."""
        self._snapshot.nav = self._orderbook.nav
        self._snapshot.allocation = self._orderbook.allocation
        self._snapshot.nav_peak = max(self._snapshot.nav_peak, self._snapshot.nav)
        self._update_max_drawdown()

    def _send_order_to_backend(self, order: OrderModel) -> None:
        """Send order data to backend via command queue.

        Args:
            order: The order model to send.
        """
        if not self._backtest or self._commands_queue is None:
            return

        order_data = order.to_api_dict()
        provider = HorizonRouterProvider()

        self._commands_queue.put(
            {
                "command": Command.EXECUTE,
                "function": provider.order_create,
                "args": {"data": order_data},
            }
        )
