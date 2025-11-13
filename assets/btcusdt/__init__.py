from typing import List

from interfaces.strategy import StrategyInterface
from services.asset import AssetService
from services.logging import LoggingService
from strategies.ema5_breakout import EMA5BreakoutStrategy


class Asset(AssetService):
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
        super().__init__(futures=True)

        self._log = LoggingService()
        self._log.setup("asset_btcusdt")

        self._strategies = [
            EMA5BreakoutStrategy(
                id="ema5_breakout",
                allocation=100_000,
                leverage=3,
                enabled=True,
            ),
        ]
