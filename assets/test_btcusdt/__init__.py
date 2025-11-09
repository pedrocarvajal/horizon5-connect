from typing import List

from interfaces.strategy import StrategyInterface
from services.asset import AssetService
from services.logging import LoggingService
from strategies.test import TestStrategy


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

        self._log = LoggingService()
        self._log.setup("asset_btcusdt")

        self._strategies = [
            TestStrategy(
                id="test",
                allocation=50_000,
                enabled=True,
            ),
        ]
