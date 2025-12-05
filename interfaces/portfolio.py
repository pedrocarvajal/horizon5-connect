"""Portfolio interface for multi-asset container."""

from abc import ABC, abstractmethod
from typing import List, Type

from interfaces.asset import AssetInterface


class PortfolioInterface(ABC):
    """Abstract interface for portfolio containing multiple trading assets."""

    _id: str
    _assets: List[Type[AssetInterface]]

    @property
    @abstractmethod
    def id(self) -> str:
        """Get portfolio identifier."""
        pass

    @property
    @abstractmethod
    def assets(self) -> List[Type[AssetInterface]]:
        """Get list of asset classes in portfolio."""
        pass
