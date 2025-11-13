from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, List

if TYPE_CHECKING:
    from interfaces.strategy import StrategyInterface
    from services.gateway import GatewayService

from models.tick import TickModel
from models.trade import TradeModel


class AssetInterface(ABC):
    @abstractmethod
    def setup(self, **kwargs: Any) -> None:
        pass

    def on_tick(self, tick: TickModel) -> None:  # noqa: B027
        pass

    def on_transaction(self, trade: TradeModel) -> None:  # noqa: B027
        pass

    def on_end(self) -> None:  # noqa: B027
        pass

    @property
    def symbol(self) -> str:
        return self._symbol

    @property
    def name(self) -> str:
        return self._name

    @property
    def gateway(self) -> "GatewayService":
        return self._gateway

    @property
    def strategies(self) -> List["StrategyInterface"]:
        return self._strategies
