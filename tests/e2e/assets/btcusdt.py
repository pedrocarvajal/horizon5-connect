from typing import List
from interfaces.strategy import StrategyInterface
from services.asset import AssetService

class BTCUSDT(AssetService):
    _symbol = 'BTCUSDT'
    _gateway_name = 'binance'
    _strategies: List[StrategyInterface]

    def __init__(self) -> None:
        super().__init__()
