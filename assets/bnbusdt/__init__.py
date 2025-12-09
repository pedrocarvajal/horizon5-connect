"""BNBUSDT asset configuration for Binance exchange trading."""

from typing import Dict, List

from enums.asset_quality_method import AssetQualityMethod
from interfaces.strategy import StrategyInterface
from services.asset import AssetService
from services.logging import LoggingService
from strategies.donchian_breakout import DonchianBreakoutStrategy
from strategies.ema5_breakout import EMA5BreakoutStrategy
from strategies.rsi_bollinger_breakout import RSIBollingerBreakoutStrategy


class Asset(AssetService):
    """BNBUSDT trading asset with configured strategies for Binance."""

    _symbol = "BNBUSDT"
    _gateway_name = "binance"
    _asset_quality_method = AssetQualityMethod.WEIGHTED_AVERAGE
    _strategies: List[StrategyInterface]

    def __init__(self, allocation: float = 0.0) -> None:
        """Initialize BNBUSDT asset with trading strategies.

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
                enabled=False,
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
            EMA5BreakoutStrategy(
                id="ema5_breakout",
                allocation=allocations.get("ema5_breakout", 0.0),
                leverage=3,
                enabled=True,
                settings={
                    "main_volume_percentage": 0.10,
                    "main_take_profit_percentage": 0.04,
                    "main_stop_loss_percentage": 0.12,
                    "recovery_maximum_number_of_openings": 3,
                    "recovery_take_profit_percentage": 0.04,
                    "recovery_stop_loss_percentage": 0.12,
                },
            ),
            RSIBollingerBreakoutStrategy(
                id="rsi_bollinger_breakout",
                allocation=allocations.get("rsi_bollinger_breakout", 0.0),
                leverage=3,
                enabled=False,
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
        """Get allocation for each enabled strategy using equal weight distribution.

        Returns:
            Dictionary mapping strategy id to allocation amount.
        """
        enabled_count = 1
        per_strategy = self._allocation / enabled_count if enabled_count > 0 else 0.0

        return {
            "donchian_breakout": per_strategy,
            "ema5_breakout": per_strategy,
            "rsi_bollinger_breakout": per_strategy,
        }
