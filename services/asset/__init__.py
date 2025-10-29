from interfaces.asset import AssetInterface
from interfaces.strategy import StrategyInterface
from models.tick import TickModel
from models.trade import TradeModel
from services.analytic import AnalyticService
from services.asset.handlers.candle import CandleHandler
from services.logging import LoggingService


class AssetService(AssetInterface):
    _strategies: list[StrategyInterface]

    def __init__(self) -> None:
        self._log = LoggingService()
        self._log.setup("asset_service")

        self._analytic = AnalyticService()
        self._candle = CandleHandler()

    def setup(self) -> None:
        self._candle.setup()
        self._analytic.setup()

        for strategy in self._strategies:
            if not strategy.enabled:
                self._log.warning(f"Strategy {strategy.name} is not enabled")
                self._strategies.remove(strategy)
                continue

            strategy.setup()

    def on_tick(self, tick: TickModel) -> None:
        self._candle.on_tick(tick)
        self._analytic.on_tick(tick)

        for strategy in self._strategies:
            strategy.on_tick(tick)

    def on_transaction(self, trade: TradeModel) -> None:
        self._analytic.on_transaction(trade)

        for strategy in self._strategies:
            strategy.on_transaction(trade)

    def on_end(self) -> None:
        self._candle.on_end()
        self._analytic.on_end()

        for strategy in self._strategies:
            strategy.on_end()

    @property
    def analytic(self) -> AnalyticService:
        return self._analytic

    @property
    def candle(self) -> CandleHandler:
        return self._candle
