"""Portfolio-level analytics service (Composite in Composite pattern)."""

from __future__ import annotations

from multiprocessing import Queue
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from vendor.enums.quality_vs_benchmark_method import QualityVsBenchmarkMethod
from vendor.enums.snapshot_event import SnapshotEvent
from vendor.models.snapshot import SnapshotModel
from vendor.services.analytic.helpers.get_quality_vs_benchmark import get_quality_vs_benchmark
from vendor.services.analytic.wrappers.analytic import AnalyticWrapper
from vendor.services.logging import LoggingService

if TYPE_CHECKING:
    from vendor.interfaces.asset import AssetInterface


class PortfolioAnalytic(AnalyticWrapper):
    """Analytics service for portfolio-level metrics aggregation.

    This is the top-level Composite component that aggregates metrics
    from its child assets (which in turn aggregate from strategies).
    NAV is calculated as sum of asset NAVs, and quality as weighted
    average of asset qualities.

    Attributes:
        _portfolio_id: Identifier of the portfolio.
        _assets: List of asset instances to aggregate from.
    """

    _assets: List[AssetInterface]
    _portfolio_id: str

    def __init__(
        self,
        portfolio_id: str,
        assets: List[AssetInterface],
        backtest: bool = False,
        backtest_id: Optional[str] = None,
        quality_vs_benchmark_method: QualityVsBenchmarkMethod = QualityVsBenchmarkMethod.FQS_BENCHMARK,
        commands_queue: Optional[Queue[Any]] = None,
    ) -> None:
        """Initialize the portfolio analytics service.

        Args:
            portfolio_id: Identifier of the portfolio being analyzed.
            assets: List of asset instances to aggregate metrics from.
            backtest: Whether running in backtest mode.
            backtest_id: Backtest identifier (required if backtest is True).
            quality_vs_benchmark_method: Method for calculating quality vs benchmark score.
            commands_queue: Queue for sending commands to external services.

        Raises:
            ValueError: If portfolio_id is empty.
            ValueError: If backtest is True but backtest_id is None.
        """
        self._log = LoggingService()

        if not portfolio_id:
            raise ValueError("Portfolio ID is required")

        if backtest and backtest_id is None:
            raise ValueError("Backtest ID is required when backtest is True")

        self._portfolio_id = portfolio_id
        self._assets = assets
        self._backtest = backtest
        self._backtest_id = backtest_id
        self._quality_vs_benchmark_method = quality_vs_benchmark_method
        self._commands_queue = commands_queue

        self._started = False
        self._started_at = None
        self._tick = None

        initial_allocation = self._calculate_initial_allocation()
        self._previous_day_nav = initial_allocation

        self._snapshot = SnapshotModel(
            strategy_id=self._portfolio_id,
            portfolio_id=self._portfolio_id,
            backtest_id=self._backtest_id,
            is_backtest=self._backtest,
            capital_allocation=initial_allocation,
            capital_nav=initial_allocation,
            capital_nav_peak=initial_allocation,
        )

    def on_end(self) -> Optional[Dict[str, Any]]:
        """Finalize analytics and generate the portfolio report.

        Collects reports from all child assets and calculates
        weighted average quality.

        Returns:
            Dictionary containing portfolio metrics and nested asset reports.
        """
        if not self._tick:
            return None

        assets_reports: Dict[str, Any] = {}

        for asset in self._assets:
            asset_report = asset.on_end()
            if asset_report:
                assets_reports[asset.symbol] = asset_report

        quality_score = self._calculate_weighted_quality(assets_reports)
        quality_vs_benchmark_score = self._calculate_quality_vs_benchmark()
        days_elapsed = self._get_elapsed_days()
        self._snapshot.score_quality = quality_score
        self._snapshot.score_quality_vs_benchmark = quality_vs_benchmark_score
        self._snapshot.time_days_elapsed = days_elapsed
        self._snapshot.event = SnapshotEvent.BACKTEST_END

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
            "portfolio_id": self._portfolio_id,
            "backtest_id": self._backtest_id,
            "is_backtest": self._backtest,
            **self._snapshot.to_dict(),
            "assets": assets_reports,
        }

        return report

    def _calculate_initial_allocation(self) -> float:
        """Calculate initial allocation from all assets.

        Returns:
            Total allocation summed from all assets.
        """
        total_allocation = 0.0
        for asset in self._assets:
            total_allocation += asset.allocation
        return total_allocation

    def _calculate_weighted_quality(self, assets_reports: Dict[str, Any]) -> float:
        """Calculate weighted average quality from asset reports.

        Args:
            assets_reports: Dictionary of asset reports with quality scores.

        Returns:
            Weighted average quality score based on allocation.
        """
        total_allocation = 0.0
        weighted_quality_sum = 0.0

        for asset in self._assets:
            asset_allocation = asset.allocation
            asset_report = assets_reports.get(asset.symbol, {})
            asset_quality = asset_report.get("score_quality", 0.0)

            if asset_allocation > 0:
                weighted_quality_sum += asset_quality * asset_allocation
                total_allocation += asset_allocation

        if total_allocation > 0:
            return round(weighted_quality_sum / total_allocation, 4)

        return 0.0

    def _calculate_quality_vs_benchmark(self) -> float:
        """Calculate quality score comparing portfolio performance against benchmark.

        Uses aggregated NAV history from all assets/strategies in this portfolio
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
        total_orders = 0
        total_buy_orders = 0
        total_sell_orders = 0

        for asset in self._assets:
            for strategy in asset.strategies:
                strategy_allocation = strategy.allocation
                strategy_snapshot = strategy.analytic.snapshot

                if strategy_allocation > 0:
                    weighted_profit_factor += strategy_snapshot.trade_profit_factor * strategy_allocation
                    weighted_win_ratio += strategy_snapshot.trade_win_ratio * strategy_allocation
                    weighted_avg_trade_duration += strategy_snapshot.trade_average_duration * strategy_allocation
                    total_allocation += strategy_allocation

                total_orders += strategy_snapshot.trade_total_orders
                total_buy_orders += strategy_snapshot.trade_buy_orders
                total_sell_orders += strategy_snapshot.trade_sell_orders

        if total_allocation > 0:
            self._snapshot.trade_profit_factor = weighted_profit_factor / total_allocation
            self._snapshot.trade_win_ratio = weighted_win_ratio / total_allocation
            self._snapshot.trade_average_duration = weighted_avg_trade_duration / total_allocation

        self._snapshot.trade_total_orders = total_orders
        self._snapshot.trade_buy_orders = total_buy_orders
        self._snapshot.trade_sell_orders = total_sell_orders

    def _refresh(self) -> None:
        """Refresh snapshot by aggregating NAV from all strategies in all assets."""
        aggregated_nav = 0.0
        aggregated_balance = 0.0

        for asset in self._assets:
            for strategy in asset.strategies:
                aggregated_nav += strategy.nav
                aggregated_balance += strategy.analytic.snapshot.capital_balance

        self._snapshot.capital_nav = aggregated_nav
        self._snapshot.capital_nav_peak = max(self._snapshot.capital_nav_peak, self._snapshot.capital_nav)
        self._snapshot.capital_balance = aggregated_balance
        self._snapshot.capital_balance_peak = max(self._snapshot.capital_balance_peak, self._snapshot.capital_balance)
        self._update_max_drawdown()
