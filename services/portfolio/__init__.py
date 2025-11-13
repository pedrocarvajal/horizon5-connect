from typing import List, Optional, Type

from interfaces.asset import AssetInterface
from interfaces.portfolio import PortfolioInterface
from models.backtest_settings import BacktestSettingsModel


class PortfolioService(PortfolioInterface):
    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    _assets: List[Type[AssetInterface]]
    _backtest_settings: Optional[BacktestSettingsModel]

    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(self) -> None:
        self._assets = []
        self._backtest_settings = None

    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def setup_backtest(self) -> None:
        self._backtest_settings = None

    # ───────────────────────────────────────────────────────────
    # GETTERS
    # ───────────────────────────────────────────────────────────
    @property
    def assets(self) -> List[AssetInterface]:
        return self._assets

    @property
    def backtest_settings(self) -> Optional[BacktestSettingsModel]:
        return self._backtest_settings
