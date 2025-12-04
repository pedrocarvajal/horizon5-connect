"""Strategy interface for trading logic implementation."""

from abc import ABC, abstractmethod
from typing import Any

from models.order import OrderModel
from models.tick import TickModel


class StrategyInterface(ABC):
    """Abstract interface (see implementations for details)."""

    _id: str
    _name: str
    _enabled: bool

    @abstractmethod
    def setup(self, **kwargs: Any) -> None:
        """Abstract method."""
        pass

    def on_tick(self, tick: TickModel) -> None:  # noqa: B027
        """Abstract method."""
        pass

    def on_new_minute(self) -> None:  # noqa: B027
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

    @property
    def id(self) -> str:
        """Abstract method (see implementations for details)."""
        return self._id

    @property
    def name(self) -> str:
        """Abstract method (see implementations for details)."""
        return self._name

    @property
    def enabled(self) -> bool:
        """Abstract method (see implementations for details)."""
        return self._enabled
