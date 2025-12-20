"""Donchian Breakout isolated test portfolio for prop firm evaluation."""

from typing import List

from strategies.donchian_breakout import DonchianBreakoutStrategy
from vendor.enums.asset_quality_method import AssetQualityMethod
from vendor.interfaces.strategy import StrategyInterface
from vendor.services.asset import AssetService
from vendor.services.portfolio import PortfolioService


class Asset(AssetService):
    """XAUUSD asset with only Donchian Breakout for testing."""

    _symbol = "XAUUSD"
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
            DonchianBreakoutStrategy(
                id="donchian_breakout",
                allocation=0.0,
                enabled=True,
                settings={
                    "volume_percentage": 0.62,
                    "sma_period": 200,
                    "donchian_entry_period": 20,
                    "donchian_exit_period": 20,
                    "adx_period": 25,
                    "atr_period": 16,
                    "adx_threshold": 15.0,
                    "take_profit_atr_multiplier": 2.5,
                    "stop_loss_atr_multiplier": 1.5,
                    "trailing_enabled": True,
                    "dynamic_atr": False,
                },
            ),
        ]

    def _setup_allocation(self) -> None:
        enabled_strategies = [s for s in self._strategies if s.enabled]
        allocation_per_strategy = self.allocation / max(len(enabled_strategies), 1)
        for strategy in enabled_strategies:
            strategy.allocation = allocation_per_strategy


class Portfolio(PortfolioService):
    """Donchian Breakout test portfolio."""

    _id = "donchian-test"
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
