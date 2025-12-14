"""XAUUSD asset configuration for MetaAPI/MetaTrader exchange trading."""

from typing import List

from strategies.ema5_breakout import EMA5BreakoutStrategy
from strategies.ema5_breakout.enums import OrderOpeningMode
from vendor.enums.asset_quality_method import AssetQualityMethod
from vendor.interfaces.strategy import StrategyInterface
from vendor.services.asset import AssetService


class Asset(AssetService):
    """XAUUSD (Gold) trading asset with EMA5 breakout strategy for MetaTrader."""

    _symbol = "XAUUSD"
    _gateway_name = "metaapi"
    _asset_quality_method = AssetQualityMethod.WEIGHTED_AVERAGE
    _strategies: List[StrategyInterface]

    def __init__(self, allocation: float = 0.0, leverage: int = 100) -> None:
        """Initialize XAUUSD asset with EMA5 breakout strategy.

        Args:
            allocation: Total allocation for this asset to distribute among strategies.
            leverage: Leverage multiplier for trading (default: 100 for forex/commodities).
        """
        super().__init__(allocation=allocation, leverage=leverage)

        self._setup_strategies()
        self._setup_allocation()

    def _setup_strategies(self) -> None:
        self._strategies = [
            EMA5BreakoutStrategy(
                id="ema5_breakout",
                allocation=0.0,
                enabled=True,
                settings={
                    "order_opening_mode": OrderOpeningMode.ONE_PER_DAY,
                    "volume_percentage": 0.05,
                    "ema_period": 6,
                    "ma_trend_period": 200,
                    "stop_loss_percentage": 0.02,
                    "trailing_activation_percentage": 0.01,
                },
            ),
        ]

    def _setup_allocation(self) -> None:
        enabled_strategies = [s for s in self._strategies if s.enabled]
        allocation_per_strategy = self.allocation / max(len(enabled_strategies), 1)

        for strategy in enabled_strategies:
            strategy.allocation = allocation_per_strategy
