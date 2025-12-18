"""Propfirm test portfolio - isolated EMA5 Breakout strategy for optimization."""

from typing import List

from strategies.ema5_breakout import EMA5BreakoutStrategy
from vendor.enums.asset_quality_method import AssetQualityMethod
from vendor.enums.tp_sl_method import TpSlMethod
from vendor.interfaces.strategy import StrategyInterface
from vendor.services.asset import AssetService
from vendor.services.portfolio import PortfolioService


class Asset(AssetService):
    """XAUUSD asset with only EMA5 Breakout for propfirm testing."""

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
            EMA5BreakoutStrategy(
                id="ema5_breakout",
                allocation=0.0,
                enabled=True,
                settings={
                    "entry_allow_multiple": False,
                    "entry_waiting_time": 0,
                    "entry_volume": 0.22,
                    "entry_ema_period": 5,
                    "main_take_profit": 3,
                    "main_take_profit_method": TpSlMethod.FIXED,
                    "main_stop_loss": 12,
                    "main_stop_loss_method": TpSlMethod.FIXED,
                    "recovery_enabled": True,
                    "recovery_maximum_layers": 3,
                    "recovery_stop_loss": 12,
                    "recovery_stop_loss_method": TpSlMethod.FIXED,
                    "recovery_take_profit": 5,
                    "recovery_take_profit_method": TpSlMethod.FIXED,
                },
            ),
        ]

    def _setup_allocation(self) -> None:
        enabled_strategies = [s for s in self._strategies if s.enabled]
        allocation_per_strategy = self.allocation / max(len(enabled_strategies), 1)
        for strategy in enabled_strategies:
            strategy.allocation = allocation_per_strategy


class Portfolio(PortfolioService):
    """Propfirm test portfolio for EMA5 Breakout optimization."""

    _id = "propfirm-test"
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
