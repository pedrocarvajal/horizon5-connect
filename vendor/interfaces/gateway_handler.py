"""Gateway handler interface for order execution."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Dict

from vendor.models.order import OrderModel

if TYPE_CHECKING:
    from vendor.interfaces.gateway import GatewayInterface
    from vendor.services.orderbook.models import OrderSyncResult


class GatewayHandlerInterface(ABC):
    """Abstract interface for gateway handler implementations."""

    _backtest: bool
    _gateway: "GatewayInterface"

    @abstractmethod
    def place_order(self, order: OrderModel) -> bool:
        """Place an order on the exchange gateway."""
        pass

    @abstractmethod
    def close_position(self, order: OrderModel) -> bool:
        """Close a position on the exchange gateway."""
        pass

    @abstractmethod
    def cancel_order(self, order: OrderModel) -> bool:
        """Cancel an order on the exchange gateway."""
        pass

    @abstractmethod
    def sync_orders(
        self,
        open_orders: Dict[str, OrderModel],
    ) -> Dict[str, "OrderSyncResult"]:
        """Sync orders with gateway and return update results."""
        pass

    @abstractmethod
    def update_order(self, order: OrderModel) -> "OrderSyncResult":
        """Update a single order's state from gateway."""
        pass

    @property
    def backtest(self) -> bool:
        """Return whether running in backtest mode."""
        return self._backtest

    @property
    def gateway(self) -> "GatewayInterface":
        """Return the gateway service instance."""
        return self._gateway
