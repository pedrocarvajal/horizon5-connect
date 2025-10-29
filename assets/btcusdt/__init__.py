from models.tick import TickModel
from models.trade import TradeModel
from services.asset import AssetService


class BTCUSDT(AssetService):
    _symbol = "BTCUSDT"
    _gateway = "binance"

    def __init__(self) -> None:
        super().__init__()

    def setup(self) -> None:
        super().setup()

    def on_tick(self, tick: TickModel) -> None:
        super().on_tick(tick)

    def on_transaction(self, trade: TradeModel) -> None:
        super().on_transaction(trade)

    def on_end(self) -> None:
        super().on_end()
