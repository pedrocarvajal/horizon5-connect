"""Asset interface for trading instrument abstraction."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, List

if TYPE_CHECKING:
    from vendor.interfaces.gateway import GatewayInterface
    from vendor.interfaces.strategy import StrategyInterface

from vendor.models.tick import TickModel


class AssetInterface(ABC):
    """Abstract interface (see implementations for details)."""

    @abstractmethod
    def __init__(self, allocation: float = 0.0) -> None:
        """Initialize the asset with allocation.

        Args:
            allocation: Total allocation for this asset.
        """
        pass

    @abstractmethod
    def on_end(self) -> Dict[str, Any]:
        """Abstract method.

        Returns:
            Asset report with aggregated performance and strategy reports.
        """
        pass

    def on_new_day(self) -> None:  # noqa: B027
        """Handle a new day event."""
        pass

    def on_new_hour(self) -> None:  # noqa: B027
        """Handle a new hour event."""
        pass

    def on_new_minute(self) -> None:  # noqa: B027
        """Handle a new minute event."""
        pass

    def on_new_month(self) -> None:  # noqa: B027
        """Handle a new month event."""
        pass

    def on_new_week(self) -> None:  # noqa: B027
        """Handle a new week event."""
        pass

    def on_tick(self, tick: TickModel) -> None:  # noqa: B027
        """Abstract method."""
        pass

    @abstractmethod
    def setup(self, **kwargs: Any) -> None:
        """Abstract method."""
        pass

    def start_historical_filling(self) -> None:  # noqa: B027
        """Abstract method."""
        pass

    def stop_historical_filling(self) -> None:  # noqa: B027
        """Abstract method."""
        pass

    @property
    @abstractmethod
    def allocation(self) -> float:
        """Return the asset allocation."""
        pass

    @property
    @abstractmethod
    def enabled(self) -> bool:
        """Return whether asset is enabled."""
        pass

    @property
    @abstractmethod
    def gateway(self) -> "GatewayInterface":
        """Return the gateway for this asset."""
        pass

    @property
    @abstractmethod
    def is_historical_filling(self) -> bool:
        """Return whether the asset is currently processing historical data."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the asset display name."""
        pass

    @property
    @abstractmethod
    def strategies(self) -> List["StrategyInterface"]:
        """Return the strategies for this asset."""
        pass

    @property
    @abstractmethod
    def symbol(self) -> str:
        """Return the trading symbol."""
        pass

    @property
    @abstractmethod
    def leverage(self) -> int:
        """Return the leverage multiplier for this asset."""
        pass
