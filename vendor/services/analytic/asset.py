"""Asset-level analytics service (Composite in Composite pattern)."""

from __future__ import annotations

from multiprocessing import Queue
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from vendor.enums.quality_vs_benchmark_method import QualityVsBenchmarkMethod
from vendor.enums.snapshot_event import SnapshotEvent
from vendor.models.snapshot import SnapshotModel
from vendor.services.analytic.helpers.get_propfirm_metrics import get_propfirm_metrics
from vendor.services.analytic.helpers.get_quality_propfirm import get_quality_propfirm
from vendor.services.analytic.helpers.get_quality_vs_benchmark import get_quality_vs_benchmark
from vendor.services.analytic.wrappers.analytic import AnalyticWrapper
from vendor.services.logging import LoggingService

if TYPE_CHECKING:
    from vendor.interfaces.strategy import StrategyInterface


class AssetAnalytic(AnalyticWrapper):
    """Analytics service for asset-level metrics aggregation.

    This is a Composite component that aggregates metrics from its
    child strategies. NAV is calculated as sum of strategy NAVs,
    and quality as weighted average of strategy qualities.

    Attributes:
        _asset_id: Symbol/identifier of the asset.
        _allocation: Total allocation for this asset.
        _strategies: List of strategy instances to aggregate from.
    """

    _allocation: float
    _asset_id: str
    _portfolio_id: Optional[str]
    _strategies: List[StrategyInterface]

    def __init__(
        self,
        asset_id: str,
        allocation: float,
        strategies: List[StrategyInterface],
        backtest: bool = False,
        backtest_id: Optional[str] = None,
        quality_vs_benchmark_method: QualityVsBenchmarkMethod = QualityVsBenchmarkMethod.FQS_BENCHMARK,
        commands_queue: Optional[Queue[Any]] = None,
        portfolio_id: Optional[str] = None,
    ) -> None:
        """Initialize the asset analytics service.

        Args:
            asset_id: Symbol/identifier of the asset being analyzed.
            allocation: Total capital allocation for this asset.
            strategies: List of strategy instances to aggregate metrics from.
            backtest: Whether running in backtest mode.
            backtest_id: Backtest identifier (required if backtest is True).
            quality_vs_benchmark_method: Method for calculating quality vs benchmark score.
            commands_queue: Queue for sending commands to external services.
            portfolio_id: Identifier of the parent portfolio.

        Raises:
            ValueError: If asset_id is empty.
            ValueError: If backtest is True but backtest_id is None.
        """
        self._log = LoggingService()

        if not asset_id:
            raise ValueError("Asset ID is required")

        if backtest and backtest_id is None:
            raise ValueError("Backtest ID is required when backtest is True")

        self._asset_id = asset_id
        self._allocation = allocation
        self._strategies = strategies
        self._backtest = backtest
        self._backtest_id = backtest_id
        self._quality_vs_benchmark_method = quality_vs_benchmark_method
        self._commands_queue = commands_queue
        self._portfolio_id = portfolio_id

        self._started = False
        self._started_at = None
        self._tick = None
        self._previous_day_nav = self._allocation

        self._snapshot = SnapshotModel(
            strategy_id=self._asset_id,
            portfolio_id=self._portfolio_id,
            asset_id=self._asset_id,
            backtest_id=self._backtest_id,
            is_backtest=self._backtest,
            capital_allocation=self._allocation,
            capital_nav=self._allocation,
            capital_nav_peak=self._allocation,
        )

    def on_new_day(self) -> None:
        """Handle a new day event. Track daily profit based on NAV change."""
        self._refresh()

        nav_change = self._snapshot.capital_nav - self._previous_day_nav
        self._snapshot.history_daily_profit.append(nav_change)

        super().on_new_day()

    def on_end(self) -> Optional[Dict[str, Any]]:
        """Finalize analytics and generate the asset report.

        Collects reports from all child strategies and calculates
        weighted average quality.

        Returns:
            Dictionary containing asset metrics and nested strategy reports.
        """
        if not self._tick:
            return None

        strategies_reports: Dict[str, Any] = {}

        for strategy in self._strategies:
            strategy_report = strategy.on_end()
            if strategy_report is not None:
                strategies_reports[strategy.id] = strategy_report

        quality_score = self._calculate_weighted_quality(strategies_reports)
        quality_vs_benchmark_score = self._calculate_quality_vs_benchmark()
        days_elapsed = self._get_elapsed_days()
        self._snapshot.score_quality = quality_score
        self._snapshot.score_quality_vs_benchmark = quality_vs_benchmark_score
        self._snapshot.time_days_elapsed = days_elapsed
        self._snapshot.event = SnapshotEvent.BACKTEST_END

        nav_change = self._snapshot.capital_nav - self._previous_day_nav
        if nav_change != 0.0:
            self._snapshot.history_daily_profit.append(nav_change)

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
            "asset_id": self._asset_id,
            **self._snapshot.to_dict(),
            "strategies": strategies_reports,
        }

        return report

    def _calculate_weighted_quality(self, strategies_reports: Dict[str, Any]) -> float:
        """Calculate weighted average quality from strategy reports.

        Args:
            strategies_reports: Dictionary of strategy reports with quality scores.

        Returns:
            Weighted average quality score based on allocation.
        """
        total_allocation = 0.0
        weighted_quality_sum = 0.0

        for strategy in self._strategies:
            strategy_allocation = strategy.allocation
            strategy_report = strategies_reports.get(strategy.id, {})
            strategy_quality = strategy_report.get("score_quality", 0.0)

            if strategy_allocation > 0:
                weighted_quality_sum += strategy_quality * strategy_allocation
                total_allocation += strategy_allocation

        if total_allocation > 0:
            return round(weighted_quality_sum / total_allocation, 4)
        return 0.0

    def _calculate_quality_vs_benchmark(self) -> float:
        """Calculate quality score comparing asset performance against benchmark.

        Uses aggregated NAV history from all strategies in this asset
        to compare against the benchmark.

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

    def _perform_calculations(self) -> None:
        """Calculate all financial metrics from aggregated history."""
        self._perform_base_calculations()

        total_allocation = 0.0
        weighted_profit_factor = 0.0
        weighted_win_ratio = 0.0
        weighted_avg_trade_duration = 0.0
        weighted_max_trade_duration = 0.0
        weighted_overnight_ratio = 0.0
        total_orders = 0
        total_buy_orders = 0
        total_sell_orders = 0
        total_overnight_count = 0

        for strategy in self._strategies:
            strategy_allocation = strategy.allocation
            strategy_snapshot = strategy.analytic.snapshot

            if strategy_allocation > 0:
                weighted_profit_factor += strategy_snapshot.trade_profit_factor * strategy_allocation
                weighted_win_ratio += strategy_snapshot.trade_win_ratio * strategy_allocation
                weighted_avg_trade_duration += strategy_snapshot.trade_average_duration * strategy_allocation
                weighted_max_trade_duration += strategy_snapshot.trade_max_duration * strategy_allocation
                weighted_overnight_ratio += strategy_snapshot.trade_overnight_ratio * strategy_allocation
                total_allocation += strategy_allocation

            total_orders += strategy_snapshot.trade_total_orders
            total_buy_orders += strategy_snapshot.trade_buy_orders
            total_sell_orders += strategy_snapshot.trade_sell_orders
            total_overnight_count += strategy_snapshot.trade_overnight_count

        if total_allocation > 0:
            self._snapshot.trade_profit_factor = weighted_profit_factor / total_allocation
            self._snapshot.trade_win_ratio = weighted_win_ratio / total_allocation
            self._snapshot.trade_average_duration = weighted_avg_trade_duration / total_allocation
            self._snapshot.trade_max_duration = weighted_max_trade_duration / total_allocation
            self._snapshot.trade_overnight_ratio = weighted_overnight_ratio / total_allocation

        self._snapshot.trade_total_orders = total_orders
        self._snapshot.trade_buy_orders = total_buy_orders
        self._snapshot.trade_sell_orders = total_sell_orders
        self._snapshot.trade_overnight_count = total_overnight_count

    def _refresh(self) -> None:
        """Refresh snapshot by aggregating from child strategies."""
        aggregated_nav = 0.0
        aggregated_balance = 0.0

        for strategy in self._strategies:
            aggregated_nav += strategy.nav
            aggregated_balance += strategy.analytic.snapshot.capital_balance

        self._snapshot.capital_nav = aggregated_nav
        self._snapshot.capital_allocation = self._allocation
        self._snapshot.capital_nav_peak = max(self._snapshot.capital_nav_peak, self._snapshot.capital_nav)
        self._snapshot.capital_balance = aggregated_balance
        self._snapshot.capital_balance_peak = max(self._snapshot.capital_balance_peak, self._snapshot.capital_balance)
        self._update_max_drawdown()

    def _calculate_propfirm_metrics(self) -> None:
        """Calculate prop firm compliance metrics based on asset's own daily profit history."""
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
