"""Orderbook interface for order and portfolio state management."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Dict, List, Optional, Set

from vendor.enums.order_side import OrderSide
from vendor.enums.order_status import OrderStatus
from vendor.models.order import OrderModel
from vendor.models.tick import TickModel

if TYPE_CHECKING:
    from vendor.interfaces.gateway_handler import GatewayHandlerInterface


class OrderbookInterface(ABC):
    """Abstract interface."""

    _orders: Dict[str, OrderModel]
    _balance: float
    _allocation: float
    _backtest: bool
    _leverage: int
    _margin_call_active: bool
    _open_orders_index: Set[str]
    _gateway_handler: "GatewayHandlerInterface"

    @abstractmethod
    def refresh(self, tick: TickModel) -> None:
        """Abstract method."""
        pass

    @abstractmethod
    def clean(self) -> None:
        """Abstract method."""
        pass

    @abstractmethod
    def open(self, order: OrderModel) -> None:
        """Abstract method."""
        pass

    @abstractmethod
    def close(self, order: OrderModel) -> None:
        """Abstract method."""
        pass

    @abstractmethod
    def cancel(self, order: OrderModel) -> None:
        """Abstract method."""
        pass

    @abstractmethod
    def where(
        self,
        side: Optional[OrderSide] = None,
        status: Optional[OrderStatus] = None,
    ) -> List[OrderModel]:
        """Filter orders by side and/or status."""
        pass

    @property
    @abstractmethod
    def orders(self) -> List[OrderModel]:
        """Return all orders in the orderbook."""
        return list(self._orders.values())

    @property
    def balance(self) -> float:
        """Return current cash balance."""
        return self._balance

    @property
    def allocation(self) -> float:
        """Return strategy allocation percentage."""
        return self._allocation

    @property
    @abstractmethod
    def nav(self) -> float:
        """Return net asset value."""
        return self._balance + self.used_margin + self.pnl

    @property
    @abstractmethod
    def exposure(self) -> float:
        """Return total market exposure from open positions."""
        return sum(
            (order.volume * order.price) for order in self._orders.values() if order.id in self._open_orders_index
        )

    @property
    @abstractmethod
    def pnl(self) -> float:
        """Return unrealized profit and loss from open positions."""
        return sum(order.profit for order in self._orders.values() if order.id in self._open_orders_index)

    @property
    def free_margin(self) -> float:
        """Return available margin for new positions."""
        return self.equity - self.used_margin

    @property
    @abstractmethod
    def used_margin(self) -> float:
        """Return margin currently used by open positions."""
        return sum(
            (order.volume * order.price) / self._leverage
            for order in self._orders.values()
            if order.id in self._open_orders_index
        )

    @property
    def equity(self) -> float:
        """Calculate account equity as balance plus unrealized PnL."""
        return self._balance + self.pnl

    @property
    def margin_level(self) -> float:
        """Return margin level as ratio of equity to used margin."""
        if self.used_margin == 0:
            return float("inf")
        return self.equity / self.used_margin

    @property
    def gateway_handler(self) -> "GatewayHandlerInterface":
        """Return gateway handler service."""
        return self._gateway_handler

    @property
    def is_backtest(self) -> bool:
        """Return whether running in backtest mode."""
        return self._backtest

    @is_backtest.setter
    def is_backtest(self, value: bool) -> None:
        """Set backtest mode."""
        self._backtest = value

    @property
    def leverage(self) -> int:
        """Return leverage multiplier."""
        return self._leverage

    @property
    def margin_call_active(self) -> bool:
        """Return whether margin call is active."""
        return self._margin_call_active

    @margin_call_active.setter
    def margin_call_active(self, value: bool) -> None:
        """Set margin call active status."""
        self._margin_call_active = value

    @property
    def open_orders_index(self) -> Set[str]:
        """Return set of open order IDs."""
        return self._open_orders_index.copy()
