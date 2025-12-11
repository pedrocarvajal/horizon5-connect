"""Portfolio-level analytics service (Composite in Composite pattern)."""

from __future__ import annotations

import datetime
from multiprocessing import Queue
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from enums.command import Command
from enums.snapshot_event import SnapshotEvent
from interfaces.analytic import AnalyticInterface
from models.snapshot import SnapshotModel
from models.tick import TickModel
from providers.horizon_router import HorizonRouterProvider
from services.analytic.helpers.get_cagr import get_cagr
from services.analytic.helpers.get_calmar_ratio import get_calmar_ratio
from services.analytic.helpers.get_expected_shortfall import get_expected_shortfall
from services.analytic.helpers.get_r2 import get_r2
from services.analytic.helpers.get_recovery_factor import get_recovery_factor
from services.analytic.helpers.get_sharpe_ratio import get_sharpe_ratio
from services.analytic.helpers.get_sortino_ratio import get_sortino_ratio
from services.analytic.helpers.get_ulcer_index import get_ulcer_index
from services.logging import LoggingService

if TYPE_CHECKING:
    from interfaces.asset import AssetInterface


class PortfolioAnalytic(AnalyticInterface):
    """Analytics service for portfolio-level metrics aggregation.

    This is the top-level Composite component that aggregates metrics
    from its child assets (which in turn aggregate from strategies).
    NAV is calculated as sum of asset NAVs, and quality as weighted
    average of asset qualities.

    Attributes:
        _portfolio_id: Identifier of the portfolio.
        _assets: List of asset instances to aggregate from.
        _backtest: Whether running in backtest mode.
        _backtest_id: Optional backtest identifier.
        _snapshot: Current analytics snapshot.
        _started: Whether analytics tracking has started.
        _started_at: Timestamp when tracking started.
        _tick: Current market tick.
    """

    _assets: List[AssetInterface]
    _backtest: bool
    _backtest_id: Optional[str]
    _commands_queue: Optional[Queue[Any]]
    _portfolio_id: str
    _snapshot: SnapshotModel
    _started: bool
    _started_at: Optional[datetime.datetime]
    _tick: Optional[TickModel]

    _log: LoggingService

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

        self._log.info(f"[PORTFOLIO_REPORT] Portfolio: {self._portfolio_id}")
        self._log.info(f"[PORTFOLIO_REPORT] {report}")

        return report

    def on_new_day(self) -> None:
        """Handle a new day event. Refreshes aggregated metrics and sends snapshot."""
        self._refresh()
        self._snapshot.performance_history.append(self._snapshot.performance)
        self._snapshot.nav_history.append(self._snapshot.nav)
        self._perform_calculations()

        if self._tick is None:
            return

        self._snapshot.event = SnapshotEvent.ON_NEW_DAY
        snapshot_data = self._snapshot.to_dict()
        snapshot_data["created_at"] = int(self._tick.date.timestamp())
        provider = HorizonRouterProvider()

        assert self._commands_queue is not None
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

    def on_tick(self, tick: TickModel) -> None:
        """Handle a new market tick. Refreshes aggregated snapshot.

        Args:
            tick: The current market tick data.
        """
        self._tick = tick
        self._refresh()

        if not self._started:
            self._started = True
            self._started_at = self._tick.date

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

    def _get_elapsed_days(self) -> int:
        """Calculate number of days elapsed since tracking started."""
        if self._tick is None or self._started_at is None:
            return 0
        return (self._tick.date - self._started_at).days

    def _perform_calculations(self) -> None:
        """Calculate all financial metrics from aggregated history."""
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

        total_allocation = 0.0
        weighted_profit_factor = 0.0
        weighted_win_ratio = 0.0
        weighted_avg_trade_duration = 0.0

        for asset in self._assets:
            for strategy in asset.strategies:
                strategy_allocation = strategy.allocation
                strategy_snapshot = strategy.analytic.snapshot

                if strategy_allocation > 0:
                    weighted_profit_factor += strategy_snapshot.profit_factor * strategy_allocation
                    weighted_win_ratio += strategy_snapshot.win_ratio * strategy_allocation
                    weighted_avg_trade_duration += strategy_snapshot.average_trade_duration * strategy_allocation
                    total_allocation += strategy_allocation

        if total_allocation > 0:
            snapshot.profit_factor = weighted_profit_factor / total_allocation
            snapshot.win_ratio = weighted_win_ratio / total_allocation
            snapshot.average_trade_duration = weighted_avg_trade_duration / total_allocation

    def _refresh(self) -> None:
        """Refresh snapshot by aggregating NAV from all strategies in all assets."""
        aggregated_nav = 0.0

        for asset in self._assets:
            for strategy in asset.strategies:
                aggregated_nav += strategy.nav

        self._snapshot.nav = aggregated_nav
        self._snapshot.nav_peak = max(self._snapshot.nav_peak, self._snapshot.nav)

        if self._snapshot.drawdown < 0:
            self._snapshot.max_drawdown = min(
                self._snapshot.max_drawdown,
                self._snapshot.drawdown,
            )

    @property
    def nav(self) -> float:
        """Return the current net asset value (sum of all strategy NAVs)."""
        return self._snapshot.nav

    @property
    def quality(self) -> float:
        """Return the current quality score."""
        return self._snapshot.quality

    @property
    def snapshot(self) -> SnapshotModel:
        """Return the current snapshot."""
        return self._snapshot
