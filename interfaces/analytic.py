"""Analytic interface for performance metrics calculation."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from models.order import OrderModel
from models.tick import TickModel


class AnalyticInterface(ABC):
    """Interface defining the contract for analytics services that track performance metrics."""

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
