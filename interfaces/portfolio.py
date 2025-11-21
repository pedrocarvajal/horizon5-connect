from abc import ABC, abstractmethod
from typing import List, Type

from interfaces.asset import AssetInterface


class PortfolioInterface(ABC):
    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    _id: str
    _assets: List[Type[AssetInterface]]

    # ───────────────────────────────────────────────────────────
    # GETTERS
    # ───────────────────────────────────────────────────────────
    @property
    @abstractmethod
    def id(self) -> str:
        pass

    @property
    def assets(self) -> List[Type[AssetInterface]]:
        return self._assets
