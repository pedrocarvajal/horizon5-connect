"""Asset interface for trading instrument abstraction."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, List

if TYPE_CHECKING:
    from interfaces.strategy import StrategyInterface
    from models.order import OrderModel
    from services.gateway import GatewayService

from models.tick import TickModel


class AssetInterface(ABC):
    """Abstract interface (see implementations for details)."""

    _symbol: str
    _name: str
    _gateway: "GatewayService"
    _strategies: List["StrategyInterface"]

    @abstractmethod
    def setup(self, **kwargs: Any) -> None:
        """Abstract method."""
        pass

    def on_tick(self, tick: TickModel) -> None:  # noqa: B027
        """Abstract method."""
        pass

    def on_transaction(self, order: "OrderModel") -> None:  # noqa: B027
        """Abstract method."""
        pass

    def on_end(self) -> None:  # noqa: B027
        """Abstract method."""
        pass

    def start_historical_filling(self) -> None:  # noqa: B027
        """Abstract method."""
        pass

    def stop_historical_filling(self) -> None:  # noqa: B027
        """Abstract method."""
        pass

    @property
    def symbol(self) -> str:
        """Abstract method (see implementations for details)."""
        return self._symbol

    @property
    def name(self) -> str:
        """Abstract method (see implementations for details)."""
        return self._name

    @property
    def gateway(self) -> "GatewayService":
        """Abstract method (see implementations for details)."""
        return self._gateway

    @property
    def strategies(self) -> List["StrategyInterface"]:
        """Abstract method (see implementations for details)."""
        return self._strategies
