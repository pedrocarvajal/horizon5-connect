"""Analytic interface for performance metrics calculation."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, Optional

from models.order import OrderModel
from models.tick import TickModel

if TYPE_CHECKING:
    from models.snapshot import SnapshotModel


class AnalyticInterface(ABC):
    """Interface defining the contract for analytics services that track performance metrics.

    This interface supports the Composite pattern where:
    - StrategyAnalytic is a Leaf (calculates metrics from orderbook)
    - AssetAnalytic is a Composite (aggregates strategy metrics)
    - PortfolioAnalytic is a Composite (aggregates asset metrics)
    """

    @abstractmethod
    def on_end(self) -> Optional[Dict[str, Any]]:
        """Handle the end of analytics tracking.

        Returns:
            Dictionary containing the analytics report, or None if tracking failed.
        """
        pass

    def on_new_day(self) -> None:  # noqa: B027
        """Handle a new day event."""
        pass

    def on_new_hour(self) -> None:  # noqa: B027
        """Handle a new hour event."""
        pass

    def on_new_month(self) -> None:  # noqa: B027
        """Handle a new month event."""
        pass

    def on_new_week(self) -> None:  # noqa: B027
        """Handle a new week event."""
        pass

    @abstractmethod
    def on_tick(self, tick: TickModel) -> None:
        """Handle a new market tick event."""
        pass

    def on_transaction(self, order: OrderModel) -> None:  # noqa: B027
        """Handle a transaction event."""
        pass

    @property
    @abstractmethod
    def nav(self) -> float:
        """Return the current net asset value."""
        pass

    @property
    @abstractmethod
    def quality(self) -> float:
        """Return the current quality score (0-1)."""
        pass

    @property
    @abstractmethod
    def snapshot(self) -> "SnapshotModel":
        """Return the current snapshot."""
        pass
