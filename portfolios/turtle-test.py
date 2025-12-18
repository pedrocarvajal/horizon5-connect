"""Turtle Trading isolated test portfolio for prop firm optimization."""

from typing import List

from strategies.turtle_trading import TurtleTradingStrategy
from vendor.enums.asset_quality_method import AssetQualityMethod
from vendor.interfaces.strategy import StrategyInterface
from vendor.services.asset import AssetService
from vendor.services.portfolio import PortfolioService


class Asset(AssetService):
    """XAUUSD asset with only Turtle Trading for testing."""

    _symbol = "XAUUSD"
    _gateway_name = "metaapi"
    _asset_quality_method = AssetQualityMethod.WEIGHTED_AVERAGE
    _strategies: List[StrategyInterface]

    def __init__(self, allocation: float = 0.0, enabled: bool = True, leverage: int = 100) -> None:
        """Initialize asset with allocation and leverage settings."""
        super().__init__(allocation=allocation, enabled=enabled, leverage=leverage)
        self._setup_strategies()
        self._setup_allocation()

    def _setup_strategies(self) -> None:
        self._strategies = [
            TurtleTradingStrategy(
                id="turtle_trading",
                allocation=0.0,
                enabled=True,
                settings={
                    "volume_percentage": 0.25,
                    "donchian_entry_period": 100,
                    "donchian_exit_period": 35,
                    "atr_period": 20,
                    "stop_loss_atr_multiplier": 2.0,
                    "pyramid_atr_multiplier": 0.5,
                    "max_pyramid_units": 4,
                    "allow_short": False,
                },
            ),
        ]

    def _setup_allocation(self) -> None:
        enabled_strategies = [s for s in self._strategies if s.enabled]
        allocation_per_strategy = self.allocation / max(len(enabled_strategies), 1)
        for strategy in enabled_strategies:
            strategy.allocation = allocation_per_strategy


class Portfolio(PortfolioService):
    """Turtle Trading test portfolio."""

    _id = "turtle-test"
    _portfolio_quality_method = AssetQualityMethod.WEIGHTED_AVERAGE

    def __init__(self) -> None:
        """Initialize portfolio with asset configuration."""
        super().__init__()
        self.setup_assets()

    def setup_assets(self) -> None:
        """Configure portfolio assets with allocations."""
        self._assets = [
            {
                "asset": Asset,
                "allocation": 100_000,
                "enabled": True,
            },
        ]
