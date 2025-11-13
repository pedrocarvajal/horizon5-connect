from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from interfaces.asset import AssetInterface


class PortfolioInterface(ABC):
    _assets: List[AssetInterface]
    _backtest_settings: Optional[Dict[str, Any]]

    @property
    @abstractmethod
    def assets(self) -> List[AssetInterface]:
        pass
