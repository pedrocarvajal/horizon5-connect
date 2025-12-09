"""Analytic component for asset-level performance tracking."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, List, Optional

from models.snapshot import SnapshotModel
from models.tick import TickModel
from services.analytic.helpers.get_cagr import get_cagr
from services.analytic.helpers.get_calmar_ratio import get_calmar_ratio
from services.analytic.helpers.get_expected_shortfall import get_expected_shortfall
from services.analytic.helpers.get_profit_factor import get_profit_factor
from services.analytic.helpers.get_r2 import get_r2
from services.analytic.helpers.get_recovery_factor import get_recovery_factor
from services.analytic.helpers.get_sharpe_ratio import get_sharpe_ratio
from services.analytic.helpers.get_sortino_ratio import get_sortino_ratio
from services.analytic.helpers.get_ulcer_index import get_ulcer_index
from services.logging import LoggingService

if TYPE_CHECKING:
    from interfaces.strategy import StrategyInterface


class AnalyticComponent:
    """Component for tracking asset-level analytics by aggregating strategy data."""

    _allocation: float
    _asset_id: str
    _backtest: bool
    _backtest_id: Optional[str]
    _ended_at: Optional[datetime.datetime]
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
    ) -> None:
        """Initialize the analytic component.

        Args:
            asset_id: Identifier of the asset being analyzed.
            allocation: Total allocation for this asset.
            strategies: List of strategies to aggregate analytics from.
            backtest: Whether running in backtest mode.
            backtest_id: Optional backtest identifier.
        """
        self._log = LoggingService()

        self._asset_id = asset_id
        self._allocation = allocation
        self._strategies = strategies
        self._backtest = backtest
        self._backtest_id = backtest_id

        self._started = False
        self._started_at = None
        self._ended_at = None
        self._tick = None

        self._snapshot = SnapshotModel(
            backtest=self._backtest,
            backtest_id=self._backtest_id,
            strategy_id=self._asset_id,
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
        )

    def on_tick(self, tick: TickModel) -> None:
        """Handle a new market tick event.

        Args:
            tick: The current market tick data.
        """
        self._tick = tick

        if not self._started:
            self._started = True
            self._started_at = self._tick.date

    def on_new_hour(self) -> None:
        """Handle a new hour event."""
        pass

    def on_new_day(self) -> None:
        """Handle a new day event."""
        self._refresh()
        self._snapshot.performance_history.append(self._snapshot.performance)
        self._snapshot.nav_history.append(self._snapshot.nav)
        self._perform_calculations()

    def on_new_week(self) -> None:
        """Handle a new week event."""
        pass

    def on_new_month(self) -> None:
        """Handle a new month event."""
        pass

    def _refresh(self) -> None:
        """Refresh snapshot data by aggregating from strategies."""
        aggregated_nav = 0.0
        aggregated_profit_history: List[float] = []

        for strategy in self._strategies:
            aggregated_nav += strategy.nav
            aggregated_profit_history.extend(strategy.analytic.snapshot.profit_history)

        self._snapshot.nav = aggregated_nav
        self._snapshot.allocation = self._allocation
        self._snapshot.nav_peak = max(self._snapshot.nav_peak, self._snapshot.nav)
        self._snapshot.profit_history = aggregated_profit_history

        if self._snapshot.drawdown < 0:
            self._snapshot.max_drawdown = min(
                self._snapshot.max_drawdown,
                self._snapshot.drawdown,
            )

    def _perform_calculations(self) -> None:
        """Calculate all financial metrics and update the snapshot."""
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

    @property
    def _elapsed_days(self) -> int:
        """Calculate the number of days elapsed since tracking started."""
        if self._tick is None or self._started_at is None:
            return 0

        return (self._tick.date - self._started_at).days

    @property
    def snapshot(self) -> SnapshotModel:
        """Return the current snapshot."""
        return self._snapshot
