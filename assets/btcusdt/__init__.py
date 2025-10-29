from interfaces.strategy import StrategyInterface
from services.asset import AssetService
from strategies.ema5_breakout import EMA5BreakoutStrategy


class BTCUSDT(AssetService):
    _symbol = "BTCUSDT"
    _gateway = "binance"
    _strategies: list[type[StrategyInterface]]

    def __init__(self) -> None:
        super().__init__()

        self._strategies = [EMA5BreakoutStrategy()]
