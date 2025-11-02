from abc import ABC, abstractmethod

from models.tick import TickModel
from models.trade import TradeModel


class AssetInterface(ABC):
    @abstractmethod
    def setup(self) -> None:
        pass

    @abstractmethod
    def on_tick(self, tick: TickModel) -> None:
        pass

    @abstractmethod
    def on_transaction(self, trade: TradeModel) -> None:
        pass

    @abstractmethod
    def on_end(self) -> None:
        pass
