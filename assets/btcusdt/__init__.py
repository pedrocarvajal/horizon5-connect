from models.tick import TickModel
from services.asset import AssetService


class BTCUSDT(AssetService):
    _symbol = "BTCUSDT"
    _gateway = "binance"

    def __init__(self) -> None:
        super().__init__()

    def on_init(self) -> None:
        super().on_init()

    def on_tick(self, tick: TickModel) -> None:
        super().on_tick(tick)
