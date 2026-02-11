"""Portfolio analytic component for initializing analytics service."""

from __future__ import annotations

from multiprocessing import Queue
from typing import TYPE_CHECKING, Any, List, Optional

from vendor.services.analytic import PortfolioAnalytic

if TYPE_CHECKING:
    from vendor.interfaces.asset import AssetInterface


class AnalyticComponent(PortfolioAnalytic):
    """Component responsible for portfolio analytics initialization."""

    def __init__(
        self,
        portfolio_id: str,
        assets: List[AssetInterface],
        backtest_id: Optional[str] = None,
        commands_queue: Optional[Queue[Any]] = None,
    ) -> None:
        """Initialize analytic component for portfolio."""
        super().__init__(
            portfolio_id=portfolio_id,
            assets=assets,
            backtest_id=backtest_id,
            commands_queue=commands_queue,
        )
