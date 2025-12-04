"""Analytic interface for performance metrics calculation."""

from abc import ABC, abstractmethod

from models.order import OrderModel
from models.tick import TickModel


class AnalyticInterface(ABC):
    """Abstract interface (see implementations for details)."""

    @abstractmethod
    def on_tick(self, tick: TickModel) -> None:
        """Abstract method."""
        pass

    def on_new_hour(self) -> None:  # noqa: B027
        """Abstract method."""
        pass

    def on_new_day(self) -> None:  # noqa: B027
        """Abstract method."""
        pass

    def on_new_week(self) -> None:  # noqa: B027
        """Abstract method."""
        pass

    def on_new_month(self) -> None:  # noqa: B027
        """Abstract method."""
        pass

    def on_transaction(self, order: OrderModel) -> None:  # noqa: B027
        """Abstract method."""
        pass

    def on_end(self) -> None:  # noqa: B027
        """Abstract method."""
        pass
