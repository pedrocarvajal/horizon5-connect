from typing import List, Type

from interfaces.asset import AssetInterface
from interfaces.portfolio import PortfolioInterface


class PortfolioService(PortfolioInterface):
    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    _assets: List[Type[AssetInterface]]

    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(self) -> None:
        self._assets = []

    # ───────────────────────────────────────────────────────────
    # GETTERS
    # ───────────────────────────────────────────────────────────
    @property
    def assets(self) -> List[AssetInterface]:
        return self._assets
