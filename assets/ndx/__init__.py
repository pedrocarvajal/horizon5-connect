"""NDX (Nasdaq 100) asset configuration for MetaAPI/Darwinex trading."""

from typing import List

from strategies.ibs import IBSStrategy
from vendor.enums.asset_quality_method import AssetQualityMethod
from vendor.interfaces.strategy import StrategyInterface
from vendor.services.asset import AssetService


class Asset(AssetService):
    """NDX (Nasdaq 100) trading asset with IBS mean reversion strategy for Darwinex."""

    _symbol = "NDX"
    _gateway_name = "metaapi"
    _asset_quality_method = AssetQualityMethod.WEIGHTED_AVERAGE
    _strategies: List[StrategyInterface]

    def __init__(self, allocation: float = 0.0, enabled: bool = True, leverage: int = 20) -> None:
        """Initialize NDX asset with IBS strategy.

        Args:
            allocation: Total allocation for this asset to distribute among strategies.
            enabled: Whether this asset is enabled for execution.
            leverage: Leverage multiplier for trading (default: 10 for indices).
        """
        super().__init__(allocation=allocation, enabled=enabled, leverage=leverage)

        self._setup_strategies()
        self._setup_allocation()

    def _setup_strategies(self) -> None:
        self._strategies = [
            IBSStrategy(
                id="ibs",
                allocation=0.0,
                enabled=True,
                settings={
                    "volume_percentage": 2.0,
                    "ibs_threshold": 0.25,
                    "max_holding_bars": 3,
                    "adx_period": 14,
                    "adx_threshold": 20.0,
                    "use_adx_filter": True,
                    "stop_loss_percentage": 0.015,
                },
            ),
        ]

    def _setup_allocation(self) -> None:
        enabled_strategies = [s for s in self._strategies if s.enabled]
        allocation_per_strategy = self.allocation / max(len(enabled_strategies), 1)

        for strategy in enabled_strategies:
            strategy.allocation = allocation_per_strategy
