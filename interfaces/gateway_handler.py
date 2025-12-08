"""Gateway handler interface for order execution."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from models.order import OrderModel

if TYPE_CHECKING:
    from interfaces.gateway import GatewayInterface


class GatewayHandlerInterface(ABC):
    """Abstract interface (see implementations for details)."""

    _backtest: bool
    _gateway: "GatewayInterface"

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

    @property
    def backtest(self) -> bool:
        """Return whether running in backtest mode."""
        return self._backtest

    @property
    def gateway(self) -> "GatewayInterface":
        """Return the gateway service instance."""
        return self._gateway
