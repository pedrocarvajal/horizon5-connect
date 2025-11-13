from abc import ABC, abstractmethod

from models.tick import TickModel
from models.trade import TradeModel


class AssetInterface(ABC):
    @abstractmethod
    def setup(self) -> None:
        pass

    def on_tick(self, tick: TickModel) -> None:  # noqa: B027
        pass

    def on_transaction(self, trade: TradeModel) -> None:  # noqa: B027
        pass

    def on_end(self) -> None:  # noqa: B027
        pass
