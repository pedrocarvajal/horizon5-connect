"""Strategy interface for trading logic implementation."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from models.order import OrderModel
from models.tick import TickModel

if TYPE_CHECKING:
    from interfaces.analytic import AnalyticInterface
    from interfaces.asset import AssetInterface
    from interfaces.orderbook import OrderbookInterface


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
    def asset(self) -> "AssetInterface":
        """Return the asset this strategy trades."""
        assert self._asset is not None
        return self._asset

    @property
    @abstractmethod
    def balance(self) -> float:
        """Return current cash balance."""
        assert self._orderbook is not None
        return self._orderbook.balance

    @property
    @abstractmethod
    def exposure(self) -> float:
        """Return total market exposure."""
        assert self._orderbook is not None
        return self._orderbook.exposure

    @property
    @abstractmethod
    def is_available_to_open_orders(self) -> bool:
        """Return whether strategy can open new orders."""
        return self.backtest or (self.is_live and not self.asset.is_historical_filling)

    @property
    @abstractmethod
    def is_live(self) -> bool:
        """Return whether strategy is in live trading mode."""
        return False

    @property
    @abstractmethod
    def nav(self) -> float:
        """Return net asset value."""
        assert self._orderbook is not None
        return self._orderbook.nav

    @property
    @abstractmethod
    def orderbook(self) -> "OrderbookInterface":
        """Return the orderbook managing this strategy's orders."""
        assert self._orderbook is not None
        return self._orderbook

    @property
    @abstractmethod
    def orders(self) -> List[OrderModel]:
        """Return all orders for this strategy."""
        assert self._orderbook is not None
        return self._orderbook.orders

    @property
    @abstractmethod
    def analytic(self) -> "AnalyticInterface":
        """Return the analytic service for this strategy."""
        assert self._analytic is not None
        return self._analytic
