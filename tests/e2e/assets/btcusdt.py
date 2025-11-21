from typing import List

from interfaces.strategy import StrategyInterface
from services.asset import AssetService


class BTCUSDT(AssetService):
    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    _symbol = "BTCUSDT"
    _gateway_name = "binance"
    _strategies: List[StrategyInterface]

    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(self) -> None:
        super().__init__()
