"""Strategy interface for trading logic implementation."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from vendor.models.order import OrderModel
from vendor.models.tick import TickModel

if TYPE_CHECKING:
    from vendor.interfaces.analytic import AnalyticInterface
    from vendor.interfaces.asset import AssetInterface
    from vendor.interfaces.orderbook import OrderbookInterface


class StrategyInterface(ABC):
    """Abstract interface (see implementations for details)."""

    _id: str
    _name: str
    _allocation: float
    _enabled: bool
    _backtest: bool
    _analytic: Optional["AnalyticInterface"]
    _asset: Optional["AssetInterface"]
    _orderbook: Optional["OrderbookInterface"]

    @abstractmethod
    def setup(self, **kwargs: Any) -> None:
        """Abstract method."""
        pass

    def on_tick(self, tick: TickModel) -> None:  # noqa: B027
        """Abstract method."""
        pass

    def on_new_minute(self) -> None:  # noqa: B027
        """Abstract method."""
        pass

    def on_new_hour(self) -> None:  # noqa: B027
        """Abstract method."""
        pass

    def on_new_day(self) -> None:  # noqa: B027
        """Abstract method."""
        pass

    def on_new_week(self) -> None:  # noqa: B027
        """Abstract method."""
        pass

    def on_new_month(self) -> None:  # noqa: B027
        """Abstract method."""
        pass

    def on_transaction(self, order: OrderModel) -> None:  # noqa: B027
        """Abstract method."""
        pass

    def on_end(self) -> Optional[Dict[str, Any]]:  # noqa: B027
        """Abstract method.

        Returns:
            Dictionary containing the analytics report, or None.
        """
        pass

    @property
    def id(self) -> str:
        """Return strategy unique identifier."""
        return self._id

    @property
    def name(self) -> str:
        """Return strategy display name."""
        return self._name

    @property
    def enabled(self) -> bool:
        """Return whether strategy is enabled."""
        return self._enabled

    @property
    def allocation(self) -> float:
        """Return strategy allocation."""
        return self._allocation

    @allocation.setter
    def allocation(self, value: float) -> None:
        """Set strategy allocation."""
        self._allocation = value

    @property
    def backtest(self) -> bool:
        """Return whether strategy is running in backtest mode."""
        return self._backtest

    @property
    @abstractmethod
    def analytic(self) -> "AnalyticInterface":
        """Return the analytic service for this strategy."""
        pass

    @property
    @abstractmethod
    def asset(self) -> "AssetInterface":
        """Return the asset this strategy trades."""
        pass

    @property
    @abstractmethod
    def balance(self) -> float:
        """Return current cash balance."""
        pass

    @property
    @abstractmethod
    def exposure(self) -> float:
        """Return total market exposure."""
        pass

    @property
    @abstractmethod
    def is_available_to_open_orders(self) -> bool:
        """Return whether strategy can open new orders."""
        pass

    @property
    @abstractmethod
    def is_live(self) -> bool:
        """Return whether strategy is in live trading mode."""
        pass

    @property
    @abstractmethod
    def leverage(self) -> int:
        """Return the leverage multiplier for this strategy."""
        pass

    @property
    @abstractmethod
    def nav(self) -> float:
        """Return net asset value."""
        pass

    @property
    @abstractmethod
    def orderbook(self) -> "OrderbookInterface":
        """Return the orderbook managing this strategy's orders."""
        pass

    @property
    @abstractmethod
    def orders(self) -> List[OrderModel]:
        """Return all orders for this strategy."""
        pass
