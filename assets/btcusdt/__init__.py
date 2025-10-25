from interfaces.asset import AssetInterface
from models.tick import TickModel


class BTCUSDT(AssetInterface):
    _symbol = "BTCUSDT"

    def __init__(self) -> None:
        super().__init__()

    def on_init(self) -> None:
        super().on_init()

    def on_tick(self, tick: TickModel) -> None:
        super().on_tick(tick)

        # self.log.info(f"Tick at {tick.date}: {tick.price}")
