"""IBS isolated test portfolio for prop firm optimization."""

from typing import List

from strategies.ibs import IBSStrategy
from vendor.enums.asset_quality_method import AssetQualityMethod
from vendor.interfaces.strategy import StrategyInterface
from vendor.services.asset import AssetService
from vendor.services.portfolio import PortfolioService


class Asset(AssetService):
    """NDX asset with only IBS strategy for testing."""

    _symbol = "NDX"
    _gateway_name = "metaapi"
    _asset_quality_method = AssetQualityMethod.WEIGHTED_AVERAGE
    _strategies: List[StrategyInterface]

    def __init__(self, allocation: float = 0.0, enabled: bool = True, leverage: int = 100) -> None:
        """Initialize asset with allocation, enabled status, and leverage."""
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
                    "volume_percentage": 0.60,
                    "ibs_threshold": 0.20,
                    "max_holding_bars": 5,
                    "adx_period": 14,
                    "adx_threshold": 20.0,
                    "use_adx_filter": True,
                    "stop_loss_percentage": 0.02,
                },
            ),
        ]

    def _setup_allocation(self) -> None:
        enabled_strategies = [s for s in self._strategies if s.enabled]
        allocation_per_strategy = self.allocation / max(len(enabled_strategies), 1)
        for strategy in enabled_strategies:
            strategy.allocation = allocation_per_strategy


class Portfolio(PortfolioService):
    """IBS test portfolio."""

    _id = "ibs-test"
    _portfolio_quality_method = AssetQualityMethod.WEIGHTED_AVERAGE

    def __init__(self) -> None:
        """Initialize portfolio and configure assets."""
        super().__init__()
        self.setup_assets()

    def setup_assets(self) -> None:
        """Configure portfolio assets with their allocations."""
        self._assets = [
            {
                "asset": Asset,
                "allocation": 100_000,
                "enabled": True,
            },
        ]
