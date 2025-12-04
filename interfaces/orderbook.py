"""Orderbook interface for order and portfolio state management."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from enums.order_side import OrderSide
from enums.order_status import OrderStatus
from models.order import OrderModel
from models.tick import TickModel


class OrderbookInterface(ABC):
    """Abstract interface."""

    _orders: Dict[str, OrderModel]
    _balance: float
    _allocation: float

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
        """Abstract method."""
        pass

    @property
    @abstractmethod
    def balance(self) -> float:
        """Abstract method."""
        pass

    @property
    @abstractmethod
    def allocation(self) -> float:
        """Abstract method."""
        pass

    @property
    @abstractmethod
    def nav(self) -> float:
        """Abstract method."""
        pass

    @property
    @abstractmethod
    def exposure(self) -> float:
        """Abstract method."""
        pass

    @property
    @abstractmethod
    def pnl(self) -> float:
        """Abstract method."""
        pass

    @property
    @abstractmethod
    def free_margin(self) -> float:
        """Abstract method."""
        pass

    @property
    @abstractmethod
    def used_margin(self) -> float:
        """Abstract method."""
        pass

    @property
    @abstractmethod
    def equity(self) -> float:
        """Abstract method."""
        pass

    @property
    @abstractmethod
    def margin_level(self) -> float:
        """Abstract method."""
        pass
