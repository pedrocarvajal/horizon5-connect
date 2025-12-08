"""Portfolio interface for multi-asset container."""

from abc import ABC
from typing import List, Tuple, Type

from interfaces.asset import AssetInterface


class PortfolioInterface(ABC):
    """Abstract interface for portfolio containing multiple trading assets."""

    _id: str
    _assets: List[Tuple[Type[AssetInterface], float]]

    @property
    def id(self) -> str:
        """Return the portfolio identifier."""
        return self._id

    @property
    def assets(self) -> List[Tuple[Type[AssetInterface], float]]:
        """Return the list of asset classes with their allocations."""
        return self._assets
