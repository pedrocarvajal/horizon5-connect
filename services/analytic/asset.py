"""Asset-level analytics service (Composite in Composite pattern)."""

from __future__ import annotations

from multiprocessing import Queue
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from models.snapshot import SnapshotModel
from services.analytic.wrappers.analytic import AnalyticWrapper
from services.logging import LoggingService

if TYPE_CHECKING:
    from interfaces.strategy import StrategyInterface


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
        self._commands_queue = commands_queue
        self._portfolio_id = portfolio_id

        self._started = False
        self._started_at = None
        self._tick = None
        self._previous_day_nav = self._allocation

        self._snapshot = SnapshotModel(
            backtest=self._backtest,
            backtest_id=self._backtest_id,
            portfolio_id=self._portfolio_id,
            strategy_id=self._asset_id,
            asset_id=self._asset_id,
            nav=self._allocation,
            allocation=self._allocation,
            nav_peak=self._allocation,
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
        """Finalize analytics and generate the asset report.

        Collects reports from all child strategies and calculates
        weighted average quality.

        Returns:
            Dictionary containing asset metrics and nested strategy reports.
        """
        strategies_reports: Dict[str, Any] = {}

        for strategy in self._strategies:
            strategy_report = strategy.on_end()
            if strategy_report is not None:
                strategies_reports[strategy.id] = strategy_report

        quality_score = self._calculate_weighted_quality(strategies_reports)
        self._snapshot.quality = quality_score

        report: Dict[str, Any] = {
            "allocation": self._snapshot.allocation,
            "nav": self._snapshot.nav,
            "performance": self._snapshot.performance,
            "performance_percentage": self._snapshot.performance_percentage,
            "max_drawdown": self._snapshot.max_drawdown,
            "quality": quality_score,
            "quality_method": "weighted_average",
            "benchmark_performance": self._snapshot.benchmark_performance,
            "benchmark_performance_percentage": self._snapshot.benchmark_performance_percentage,
            "alpha": self._snapshot.alpha,
            "beta": self._snapshot.beta,
            "correlation": self._snapshot.correlation,
            "tracking_error": self._snapshot.tracking_error,
            "information_ratio": self._snapshot.information_ratio,
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
            strategy_quality = strategy_report.get("quality", 0.0)

            if strategy_allocation > 0:
                weighted_quality_sum += strategy_quality * strategy_allocation
                total_allocation += strategy_allocation

        if total_allocation > 0:
            return round(weighted_quality_sum / total_allocation, 4)
        return 0.0

    def _perform_calculations(self) -> None:
        """Calculate all financial metrics from aggregated history."""
        self._perform_base_calculations()

        total_allocation = 0.0
        weighted_profit_factor = 0.0
        weighted_win_ratio = 0.0
        weighted_avg_trade_duration = 0.0
        total_orders = 0
        total_buy_orders = 0
        total_sell_orders = 0

        for strategy in self._strategies:
            strategy_allocation = strategy.allocation
            strategy_snapshot = strategy.analytic.snapshot

            if strategy_allocation > 0:
                weighted_profit_factor += strategy_snapshot.profit_factor * strategy_allocation
                weighted_win_ratio += strategy_snapshot.win_ratio * strategy_allocation
                weighted_avg_trade_duration += strategy_snapshot.average_trade_duration * strategy_allocation
                total_allocation += strategy_allocation

            total_orders += strategy_snapshot.total_orders
            total_buy_orders += strategy_snapshot.total_buy_orders
            total_sell_orders += strategy_snapshot.total_sell_orders

        if total_allocation > 0:
            self._snapshot.profit_factor = weighted_profit_factor / total_allocation
            self._snapshot.win_ratio = weighted_win_ratio / total_allocation
            self._snapshot.average_trade_duration = weighted_avg_trade_duration / total_allocation

        self._snapshot.total_orders = total_orders
        self._snapshot.total_buy_orders = total_buy_orders
        self._snapshot.total_sell_orders = total_sell_orders

    def _refresh(self) -> None:
        """Refresh snapshot by aggregating from child strategies."""
        aggregated_nav = 0.0

        for strategy in self._strategies:
            aggregated_nav += strategy.nav

        self._snapshot.nav = aggregated_nav
        self._snapshot.allocation = self._allocation
        self._snapshot.nav_peak = max(self._snapshot.nav_peak, self._snapshot.nav)
        self._update_max_drawdown()
