"""BTCUSDT asset configuration for Binance exchange trading."""

from typing import List

from strategies.donchian_breakout import DonchianBreakoutStrategy
from strategies.rsi_bollinger_breakout import RSIBollingerBreakoutStrategy
from vendor.enums.asset_quality_method import AssetQualityMethod
from vendor.interfaces.strategy import StrategyInterface
from vendor.services.asset import AssetService


class Asset(AssetService):
    """BTCUSDT trading asset with configured strategies for Binance."""

    _symbol = "BTCUSDT"
    _gateway_name = "binance"
    _asset_quality_method = AssetQualityMethod.WEIGHTED_AVERAGE
    _strategies: List[StrategyInterface]

    def __init__(self, allocation: float = 0.0, enabled: bool = True, leverage: int = 10) -> None:
        """Initialize BTCUSDT asset with trading strategies.

        Args:
            allocation: Total allocation for this asset to distribute among strategies.
            enabled: Whether this asset is enabled for execution.
            leverage: Leverage multiplier for trading (default: 10).
        """
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
                    "adx_threshold": 25.0,
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
