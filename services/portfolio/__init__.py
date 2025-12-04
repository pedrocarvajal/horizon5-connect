"""Portfolio service for managing collections of trading assets."""

from typing import List, Type

from interfaces.asset import AssetInterface
from interfaces.portfolio import PortfolioInterface


class PortfolioService(PortfolioInterface):
    """Service for managing a portfolio of trading assets."""

    _id: str
    _assets: List[Type[AssetInterface]]

    def __init__(self) -> None:
        """Initialize the portfolio with an empty asset list."""
        self._assets = []

    @property
    def id(self) -> str:
        """Return the portfolio identifier."""
        return self._id

    @property
    def assets(self) -> List[Type[AssetInterface]]:
        """Return the list of asset classes in this portfolio."""
        return self._assets
