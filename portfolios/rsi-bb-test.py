"""RSI Bollinger Breakout isolated test portfolio for prop firm evaluation."""

from typing import List

from strategies.rsi_bollinger_breakout import RSIBollingerBreakoutStrategy
from vendor.enums.asset_quality_method import AssetQualityMethod
from vendor.interfaces.strategy import StrategyInterface
from vendor.services.asset import AssetService
from vendor.services.portfolio import PortfolioService


class Asset(AssetService):
    """XAUUSD asset with only RSI Bollinger Breakout for testing."""

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
            RSIBollingerBreakoutStrategy(
                id="rsi_bollinger_breakout",
                allocation=0.0,
                enabled=True,
                settings={
                    "volume_percentage": 1.5,
                    "rsi_period": 10,
                    "adx_period": 14,
                    "ema_period": 150,
                    "atr_period": 20,
                    "bollinger_period": 5,
                    "bollinger_deviation": 1.7,
                    "adx_threshold": 20.0,
                    "take_profit_atr_multiplier": 3.5,
                    "stop_loss_atr_multiplier": 2.5,
                },
            ),
        ]

    def _setup_allocation(self) -> None:
        enabled_strategies = [s for s in self._strategies if s.enabled]
        allocation_per_strategy = self.allocation / max(len(enabled_strategies), 1)
        for strategy in enabled_strategies:
            strategy.allocation = allocation_per_strategy


class Portfolio(PortfolioService):
    """RSI Bollinger Breakout test portfolio."""

    _id = "rsi-bb-test"
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
