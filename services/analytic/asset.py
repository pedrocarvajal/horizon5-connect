"""Asset-level analytics service (Composite in Composite pattern)."""

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
from services.logging import LoggingService

if TYPE_CHECKING:
    from interfaces.strategy import StrategyInterface


class AssetAnalytic(AnalyticInterface):
    """Analytics service for asset-level metrics aggregation.

    This is a Composite component that aggregates metrics from its
    child strategies. NAV is calculated as sum of strategy NAVs,
    and quality as weighted average of strategy qualities.

    Attributes:
        _asset_id: Symbol/identifier of the asset.
        _allocation: Total allocation for this asset.
        _strategies: List of strategy instances to aggregate from.
        _backtest: Whether running in backtest mode.
        _backtest_id: Optional backtest identifier.
        _snapshot: Current analytics snapshot.
        _started: Whether analytics tracking has started.
        _started_at: Timestamp when tracking started.
        _tick: Current market tick.
    """

    _allocation: float
    _asset_id: str
    _backtest: bool
    _backtest_id: Optional[str]
    _commands_queue: Optional[Queue[Any]]
    _portfolio_id: Optional[str]
    _snapshot: SnapshotModel
    _started: bool
    _started_at: Optional[datetime.datetime]
    _strategies: List[StrategyInterface]
    _tick: Optional[TickModel]

    _log: LoggingService

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
            "strategies": strategies_reports,
        }

        self._log.info(f"[ASSET_REPORT] Asset: {self._asset_id}")
        self._log.info(f"[ASSET_REPORT] quality={quality_score}, allocation={self._allocation}")

        return report

    def on_new_day(self) -> None:
        """Handle a new day event. Refreshes aggregated metrics and sends snapshot."""
        self._refresh()
        self._snapshot.performance_history.append(self._snapshot.performance)
        self._snapshot.nav_history.append(self._snapshot.nav)

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

    def _refresh(self) -> None:
        """Refresh snapshot by aggregating from child strategies."""
        aggregated_nav = 0.0

        for strategy in self._strategies:
            aggregated_nav += strategy.nav

        self._snapshot.nav = aggregated_nav
        self._snapshot.allocation = self._allocation
        self._snapshot.nav_peak = max(self._snapshot.nav_peak, self._snapshot.nav)

        if self._snapshot.drawdown < 0:
            self._snapshot.max_drawdown = min(
                self._snapshot.max_drawdown,
                self._snapshot.drawdown,
            )

    @property
    def nav(self) -> float:
        """Return the current net asset value (sum of strategy NAVs)."""
        return self._snapshot.nav

    @property
    def quality(self) -> float:
        """Return the current quality score."""
        return self._snapshot.quality

    @property
    def snapshot(self) -> SnapshotModel:
        """Return the current snapshot."""
        return self._snapshot
