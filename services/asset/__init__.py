from interfaces.asset import AssetInterface
from models.tick import TickModel
from models.trade import TradeModel
from services.analytic import AnalyticService
from services.asset.handlers.candle import CandleHandler


class AssetService(AssetInterface):
    def __init__(self) -> None:
        super().__init__()

        self._analytic = AnalyticService()
        self._candle = CandleHandler()

    def setup(self) -> None:
        super().setup()
        self._candle.setup()
        self._analytic.setup()

    def on_tick(self, tick: TickModel) -> None:
        super().on_tick(tick)
        self._candle.on_tick(tick)
        self._analytic.on_tick(tick)

    def on_transaction(self, trade: TradeModel) -> None:
        super().on_transaction(trade)
        self._analytic.on_transaction(trade)

    def on_end(self) -> None:
        super().on_end()
        self._candle.on_end()
        self._analytic.on_end()

    @property
    def analytic(self) -> AnalyticService:
        return self._analytic
