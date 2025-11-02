from abc import ABC, abstractmethod

from models.order import OrderModel
from models.tick import TickModel


class AnalyticInterface(ABC):
    @abstractmethod
    def on_tick(self, tick: TickModel) -> None:
        pass

    @abstractmethod
    def on_new_hour(self) -> None:
        pass

    @abstractmethod
    def on_new_day(self) -> None:
        pass

    @abstractmethod
    def on_new_week(self) -> None:
        pass

    @abstractmethod
    def on_new_month(self) -> None:
        pass

    @abstractmethod
    def on_transaction(self, order: OrderModel) -> None:
        pass

    @abstractmethod
    def on_end(self) -> None:
        pass
