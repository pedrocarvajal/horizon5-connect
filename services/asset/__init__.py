from interfaces.asset import AssetInterface
from models.tick import TickModel
from models.trade import TradeModel
from services.analytic import AnalyticService
from services.asset.handlers.candles import CandlesHandler


class AssetService(AssetInterface):
    def __init__(self) -> None:
        super().__init__()

        self._analytic = AnalyticService()
        self._candles = CandlesHandler()

    def on_start(self) -> None:
        super().on_start()
        self._candles.on_start()
        self._analytic.on_start()

    def on_tick(self, tick: TickModel) -> None:
        super().on_tick(tick)
        self._candles.on_tick(tick)
        self._analytic.on_tick(tick)

    def on_transaction(self, trade: TradeModel) -> None:
        super().on_transaction(trade)
        self._analytic.on_transaction(trade)

    def on_end(self) -> None:
        super().on_end()
        self._candles.on_end()
        self._analytic.on_end()

    @property
    def analytic(self) -> AnalyticService:
        return self._analytic
