"""BTCUSDT asset configuration for Binance exchange trading."""

from typing import List

from interfaces.strategy import StrategyInterface
from services.asset import AssetService
from services.logging import LoggingService
from strategies.ema5_breakout import EMA5BreakoutStrategy
from strategies.test import TestStrategy


class Asset(AssetService):
    """BTCUSDT trading asset with configured strategies for Binance."""

    _symbol = "BTCUSDT"
    _gateway_name = "binance"
    _strategies: List[StrategyInterface]

    def __init__(self) -> None:
        """Initialize BTCUSDT asset with trading strategies."""
        super().__init__()

        self._log = LoggingService()
        self._log.setup("asset_btcusdt")

        self._strategies = [
            EMA5BreakoutStrategy(
                id="ema5_breakout",
                allocation=1000,
                leverage=3,
                enabled=True,
            ),
            TestStrategy(
                id="test",
                allocation=1000,
                leverage=3,
                enabled=False,
            ),
        ]
