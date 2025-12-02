from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from enums.order_side import OrderSide
from enums.order_status import OrderStatus
from models.order import OrderModel
from models.tick import TickModel


class OrderbookInterface(ABC):
    _orders: Dict[str, OrderModel]
    _balance: float
    _allocation: float

    @abstractmethod
    def refresh(self, tick: TickModel) -> None:
        pass

    @abstractmethod
    def clean(self) -> None:
        pass

    @abstractmethod
    def open(self, order: OrderModel) -> None:
        pass

    @abstractmethod
    def close(self, order: OrderModel) -> None:
        pass

    @abstractmethod
    def cancel(self, order: OrderModel) -> None:
        pass

    @abstractmethod
    def where(
        self,
        side: Optional[OrderSide] = None,
        status: Optional[OrderStatus] = None,
    ) -> List[OrderModel]:
        pass

    @property
    @abstractmethod
    def orders(self) -> List[OrderModel]:
        pass

    @property
    @abstractmethod
    def balance(self) -> float:
        pass

    @property
    @abstractmethod
    def allocation(self) -> float:
        pass

    @property
    @abstractmethod
    def nav(self) -> float:
        pass

    @property
    @abstractmethod
    def exposure(self) -> float:
        pass

    @property
    @abstractmethod
    def pnl(self) -> float:
        pass

    @property
    @abstractmethod
    def free_margin(self) -> float:
        pass

    @property
    @abstractmethod
    def used_margin(self) -> float:
        pass

    @property
    @abstractmethod
    def equity(self) -> float:
        pass

    @property
    @abstractmethod
    def margin_level(self) -> float:
        pass
