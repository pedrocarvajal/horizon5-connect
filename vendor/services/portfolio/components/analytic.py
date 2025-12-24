"""Portfolio analytic component for initializing analytics service."""

from __future__ import annotations

from multiprocessing import Queue
from typing import TYPE_CHECKING, Any, List, Optional

from vendor.services.analytic import PortfolioAnalytic

if TYPE_CHECKING:
    from vendor.interfaces.asset import AssetInterface


class AnalyticComponent:
    """Component responsible for portfolio analytics initialization."""

    _analytic: Optional[PortfolioAnalytic]

    def __init__(self) -> None:
        """Initialize the analytic component."""
        self._analytic = None

    def setup_analytic(
        self,
        portfolio_id: str,
        assets: List[AssetInterface],
        backtest: bool = False,
        backtest_id: Optional[str] = None,
        commands_queue: Optional[Queue[Any]] = None,
    ) -> PortfolioAnalytic:
        """Initialize the portfolio analytics service.

        Args:
            portfolio_id: Identifier of the portfolio.
            assets: List of asset instances.
            backtest: Whether running in backtest mode.
            backtest_id: Backtest identifier.
            commands_queue: Queue for commands.

        Returns:
            Initialized PortfolioAnalytic instance.
        """
        self._analytic = PortfolioAnalytic(
            portfolio_id=portfolio_id,
            assets=assets,
            backtest=backtest,
            backtest_id=backtest_id,
            commands_queue=commands_queue,
        )
        return self._analytic

    @property
    def analytic(self) -> Optional[PortfolioAnalytic]:
        """Return the analytics service instance."""
        return self._analytic
