"""Gateway handler interface for order execution."""

from abc import ABC, abstractmethod

from models.order import OrderModel


class GatewayHandlerInterface(ABC):
    """Abstract interface (see implementations for details)."""

    @abstractmethod
    def open_order(self, order: OrderModel) -> bool:
        """Abstract method."""
        pass

    @abstractmethod
    def close_order(self, order: OrderModel) -> bool:
        """Abstract method."""
        pass

    @abstractmethod
    def cancel_order(self, order: OrderModel) -> bool:
        """Abstract method."""
        pass
