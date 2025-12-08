"""BTCUSDT asset configuration for Binance exchange trading."""

from typing import Dict, List

from interfaces.strategy import StrategyInterface
from services.asset import AssetService
from services.logging import LoggingService
from strategies.donchian_breakout import DonchianBreakoutStrategy
from strategies.ema5_breakout import EMA5BreakoutStrategy
from strategies.test import TestStrategy


class Asset(AssetService):
    """BTCUSDT trading asset with configured strategies for Binance."""

    _symbol = "BTCUSDT"
    _gateway_name = "binance"
    _strategies: List[StrategyInterface]

    def __init__(self, allocation: float = 0.0) -> None:
        """Initialize BTCUSDT asset with trading strategies.

        Args:
            allocation: Total allocation for this asset to distribute among strategies.
        """
        super().__init__(allocation=allocation)

        self._log = LoggingService()

        allocations = self._get_allocation_by_strategy()

        self._strategies = [
            EMA5BreakoutStrategy(
                id="ema5_breakout",
                allocation=allocations.get("ema5_breakout", 0.0),
                leverage=3,
                enabled=False,
            ),
            DonchianBreakoutStrategy(
                id="donchian_breakout",
                allocation=allocations.get("donchian_breakout", 0.0),
                leverage=3,
                enabled=True,
            ),
            TestStrategy(
                id="test",
                allocation=allocations.get("test", 0.0),
                leverage=3,
                enabled=False,
            ),
        ]

    def _get_allocation_by_strategy(self) -> Dict[str, float]:
        """Get allocation for each enabled strategy using equal weight distribution.

        Returns:
            Dictionary mapping strategy id to allocation amount.
        """
        enabled_count = 1
        per_strategy = self._allocation / enabled_count if enabled_count > 0 else 0.0

        return {
            "donchian_breakout": per_strategy,
            "ema5_breakout": per_strategy,
            "test": per_strategy,
        }
