from abc import ABC, abstractmethod

from models.order import OrderModel


class GatewayHandlerInterface(ABC):
    @abstractmethod
    def open_order(self, order: OrderModel) -> bool:
        pass

    @abstractmethod
    def close_order(self, order: OrderModel) -> bool:
        pass

    @abstractmethod
    def cancel_order(self, order: OrderModel) -> bool:
        pass
