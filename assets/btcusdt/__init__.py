"""BTCUSDT asset configuration for Binance exchange trading."""

from typing import Dict, List

from enums.asset_quality_method import AssetQualityMethod
from interfaces.strategy import StrategyInterface
from services.asset import AssetService
from services.logging import LoggingService
from strategies.donchian_breakout import DonchianBreakoutStrategy
from strategies.rsi_bollinger_breakout import RSIBollingerBreakoutStrategy


class Asset(AssetService):
    """BTCUSDT trading asset with configured strategies for Binance."""

    _symbol = "BTCUSDT"
    _gateway_name = "binance"
    _asset_quality_method = AssetQualityMethod.WEIGHTED_AVERAGE
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
            DonchianBreakoutStrategy(
                id="donchian_breakout",
                allocation=allocations.get("donchian_breakout", 0.0),
                leverage=3,
                enabled=True,
                settings={
                    "volume_percentage": 0.60,
                    "sma_period": 200,
                    "donchian_entry_period": 20,
                    "donchian_exit_period": 20,
                    "adx_period": 25,
                    "atr_period": 16,
                    "adx_threshold": 20.0,
                    "take_profit_atr_multiplier": 2.5,
                    "stop_loss_atr_multiplier": 1.5,
                    "trailing_enabled": True,
                    "dynamic_atr": False,
                },
            ),
            RSIBollingerBreakoutStrategy(
                id="rsi_bollinger_breakout",
                allocation=allocations.get("rsi_bollinger_breakout", 0.0),
                leverage=3,
                enabled=True,
                settings={
                    "volume_percentage": 0.75,
                    "rsi_period": 10,
                    "adx_period": 14,
                    "ema_period": 150,
                    "atr_period": 20,
                    "bollinger_period": 5,
                    "bollinger_deviation": 1.6,
                    "adx_threshold": 22.0,
                    "take_profit_atr_multiplier": 3.8,
                    "stop_loss_atr_multiplier": 2.0,
                },
            ),
        ]

    def _get_allocation_by_strategy(self) -> Dict[str, float]:
        return {
            "donchian_breakout": 500000,
            "rsi_bollinger_breakout": 500000,
        }
