from typing import List

from interfaces.strategy import StrategyInterface
from services.asset import AssetService


class BTCUSDT(AssetService):
    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    _symbol = "BTCUSDT"
    _gateway = "binance"
    _strategies: List[type[StrategyInterface]]

    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(self) -> None:
        super().__init__()
