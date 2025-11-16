from abc import ABC
from typing import List, Type

from interfaces.asset import AssetInterface


class PortfolioInterface(ABC):
    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    _assets: List[Type[AssetInterface]]

    # ───────────────────────────────────────────────────────────
    # GETTERS
    # ───────────────────────────────────────────────────────────
    @property
    def assets(self) -> List[AssetInterface]:
        return self._assets
