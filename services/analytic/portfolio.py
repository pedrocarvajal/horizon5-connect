"""Portfolio-level analytics service (Composite in Composite pattern)."""

from __future__ import annotations

from multiprocessing import Queue
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from models.snapshot import SnapshotModel
from services.analytic.wrappers.analytic import AnalyticWrapper
from services.logging import LoggingService

if TYPE_CHECKING:
    from interfaces.asset import AssetInterface


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
        commands_queue: Optional[Queue[Any]] = None,
    ) -> None:
        """Initialize the portfolio analytics service.

        Args:
            portfolio_id: Identifier of the portfolio being analyzed.
            assets: List of asset instances to aggregate metrics from.
            backtest: Whether running in backtest mode.
            backtest_id: Backtest identifier (required if backtest is True).
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
        self._commands_queue = commands_queue

        self._started = False
        self._started_at = None
        self._tick = None

        initial_allocation = self._calculate_initial_allocation()
        self._previous_day_nav = initial_allocation

        self._snapshot = SnapshotModel(
            backtest=self._backtest,
            backtest_id=self._backtest_id,
            portfolio_id=self._portfolio_id,
            strategy_id=self._portfolio_id,
            nav=initial_allocation,
            allocation=initial_allocation,
            nav_peak=initial_allocation,
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
        """Finalize analytics and generate the portfolio report.

        Collects reports from all child assets and calculates
        weighted average quality.

        Returns:
            Dictionary containing portfolio metrics and nested asset reports.
        """
        assets_reports: Dict[str, Any] = {}

        for asset in self._assets:
            asset_report = asset.on_end()
            if asset_report:
                assets_reports[asset.symbol] = asset_report

        quality_score = self._calculate_weighted_quality(assets_reports)
        self._snapshot.quality = quality_score

        report: Dict[str, Any] = {
            "portfolio_id": self._portfolio_id,
            "allocation": self._snapshot.allocation,
            "nav": self._snapshot.nav,
            "performance": self._snapshot.performance,
            "performance_percentage": self._snapshot.performance_percentage,
            "max_drawdown": self._snapshot.max_drawdown,
            "quality": quality_score,
            "quality_method": "weighted_average",
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
            asset_quality = asset_report.get("quality", 0.0)

            if asset_allocation > 0:
                weighted_quality_sum += asset_quality * asset_allocation
                total_allocation += asset_allocation

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

        for asset in self._assets:
            for strategy in asset.strategies:
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
        """Refresh snapshot by aggregating NAV from all strategies in all assets."""
        aggregated_nav = 0.0

        for asset in self._assets:
            for strategy in asset.strategies:
                aggregated_nav += strategy.nav

        self._snapshot.nav = aggregated_nav
        self._snapshot.nav_peak = max(self._snapshot.nav_peak, self._snapshot.nav)
        self._update_max_drawdown()
