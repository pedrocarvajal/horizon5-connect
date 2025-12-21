"""XAUUSD asset configuration for MetaAPI/MetaTrader exchange trading."""

from typing import List

from strategies.ema5_breakout import EMA5BreakoutStrategy
from strategies.meb_faber_timing import MebFaberTimingStrategy
from strategies.turtle_trading import TurtleTradingStrategy
from vendor.enums.asset_quality_method import AssetQualityMethod
from vendor.enums.tp_sl_method import TpSlMethod
from vendor.interfaces.strategy import StrategyInterface
from vendor.services.asset import AssetService


class Asset(AssetService):
    """XAUUSD (Gold) trading asset with EMA5 breakout strategy for MetaTrader."""

    _symbol = "XAUUSD"
    _gateway_name = "metaapi"
    _asset_quality_method = AssetQualityMethod.WEIGHTED_AVERAGE
    _strategies: List[StrategyInterface]

    def __init__(self, allocation: float = 0.0, enabled: bool = True, leverage: int = 100) -> None:
        """Initialize XAUUSD asset with EMA5 breakout strategy.

        Args:
            allocation: Total allocation for this asset to distribute among strategies.
            enabled: Whether this asset is enabled for execution.
            leverage: Leverage multiplier for trading (default: 100 for forex/commodities).
        """
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
            TurtleTradingStrategy(
                id="turtle_trading",
                allocation=0.0,
                enabled=True,
                settings={
                    "volume_percentage": 0.09,
                    "donchian_entry_period": 55,
                    "donchian_exit_period": 20,
                    "atr_period": 20,
                    "stop_loss_atr_multiplier": 2.0,
                    "pyramid_atr_multiplier": 0.5,
                    "max_pyramid_units": 3,
                    "allow_short": False,
                },
            ),
            MebFaberTimingStrategy(
                id="meb_faber_timing",
                allocation=0.0,
                enabled=True,
                settings={
                    "volume_percentage": 1.0,
                    "sma_period": 10,
                },
            ),
        ]

    def _setup_allocation(self) -> None:
        enabled_strategies = [s for s in self._strategies if s.enabled]
        allocation_per_strategy = self.allocation / max(len(enabled_strategies), 1)

        for strategy in enabled_strategies:
            strategy.allocation = allocation_per_strategy
