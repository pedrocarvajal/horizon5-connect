"""BTCUSDT test asset for end-to-end indicator testing."""

from typing import List

from interfaces.strategy import StrategyInterface
from services.asset import AssetService


class BTCUSDT(AssetService):
    """Test asset representing the BTCUSDT trading pair on Binance."""

    _symbol = "BTCUSDT"
    _gateway_name = "binance"
    _strategies: List[StrategyInterface]
