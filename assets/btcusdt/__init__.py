from interfaces.strategy import StrategyInterface
from services.asset import AssetService
from services.logging import LoggingService
from strategies.ema5_breakout import EMA5BreakoutStrategy


class BTCUSDT(AssetService):
    _symbol = "BTCUSDT"
    _gateway = "binance"
    _strategies: list[type[StrategyInterface]]

    def __init__(self) -> None:
        super().__init__()

        self._log = LoggingService()
        self._log.setup("asset_btcusdt")

        self._strategies = [EMA5BreakoutStrategy()]
