from typing import List

from interfaces.strategy import StrategyInterface
from services.asset import AssetService
from services.logging import LoggingService
from strategies.ema5_breakout import EMA5BreakoutStrategy
from strategies.rebounds_off_supports import ReboundsOffSupportsStrategy


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
            EMA5BreakoutStrategy(
                id="ema5_breakout",
                allocation=50_000,
                enabled=False,
            ),
            ReboundsOffSupportsStrategy(
                id="rebounds_off_supports",
                allocation=50_000,
                enabled=True,
            ),
        ]
