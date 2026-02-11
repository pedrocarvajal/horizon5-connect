"""BTCUSDT asset configuration for Binance exchange trading."""

from strategies.donchian_breakout import DonchianBreakoutStrategy
from strategies.ibs import IBSStrategy
from strategies.meb_faber_timing import MebFaberTimingStrategy
from strategies.rsi_bollinger_breakout import RSIBollingerBreakoutStrategy
from strategies.turtle_trading import TurtleTradingStrategy
from vendor.services.asset import AssetService


class Asset(AssetService):
    """BTCUSDT (Bitcoin) trading asset with all strategies for Binance."""

    def __init__(self) -> None:
        super().__init__(
            symbol="BTCUSDT",
            gateway_name="binance",
            leverage=3,
            strategies=[
                DonchianBreakoutStrategy(
                    id="donchian_breakout",
                    settings={
                        "volume_percentage": 0.40,
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
                    settings={
                        "volume_percentage": 0.40,
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
                TurtleTradingStrategy(
                    id="turtle_trading",
                    settings={
                        "volume_percentage": 0.10,
                        "donchian_entry_period": 20,
                        "donchian_exit_period": 10,
                        "atr_period": 20,
                        "stop_loss_atr_multiplier": 2.0,
                        "pyramid_atr_multiplier": 0.5,
                        "max_pyramid_units": 4,
                        "allow_short": False,
                    },
                ),
                IBSStrategy(
                    id="ibs",
                    settings={
                        "volume_percentage": 0.40,
                        "ibs_threshold": 0.20,
                        "max_holding_bars": 5,
                        "adx_period": 14,
                        "adx_threshold": 20.0,
                        "use_adx_filter": True,
                        "stop_loss_percentage": 0.03,
                    },
                ),
                MebFaberTimingStrategy(
                    id="meb_faber_timing",
                    settings={
                        "volume_percentage": 0.40,
                        "sma_period": 10,
                    },
                ),
            ],
        )
