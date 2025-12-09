"""Asset interface for trading instrument abstraction."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, List

if TYPE_CHECKING:
    from interfaces.gateway import GatewayInterface
    from interfaces.strategy import StrategyInterface
    from models.order import OrderModel

from models.tick import TickModel


class AssetInterface(ABC):
    """Abstract interface (see implementations for details)."""

    _symbol: str
    _name: str
    _allocation: float
    _enabled: bool
    _is_historical_filling: bool
    _gateway: "GatewayInterface"
    _strategies: List["StrategyInterface"]

    @abstractmethod
    def __init__(self, allocation: float = 0.0) -> None:
        """Initialize the asset with allocation.

        Args:
            allocation: Total allocation for this asset.
        """
        pass

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

    def on_end(self) -> Dict[str, Any]:
        """Abstract method.

        Returns:
            Asset report with aggregated performance and strategy reports.
        """
        return {}

    def start_historical_filling(self) -> None:  # noqa: B027
        """Abstract method."""
        pass

    def stop_historical_filling(self) -> None:  # noqa: B027
        """Abstract method."""
        pass

    @property
    def symbol(self) -> str:
        """Return the trading symbol."""
        return self._symbol

    @property
    def name(self) -> str:
        """Return the asset display name."""
        return self._name

    @property
    def allocation(self) -> float:
        """Return the asset allocation."""
        return self._allocation

    @property
    def enabled(self) -> bool:
        """Return whether asset is enabled."""
        return self._enabled

    @property
    def gateway(self) -> "GatewayInterface":
        """Return the gateway for this asset."""
        return self._gateway

    @property
    def strategies(self) -> List["StrategyInterface"]:
        """Return the strategies for this asset."""
        return self._strategies

    @property
    def is_historical_filling(self) -> bool:
        """Return whether the asset is currently processing historical data."""
        return self._is_historical_filling
