from structs.tick import Tick
from structs.trade import Trade


class AssetInterface:
    def init(self) -> None:
        pass

    def on_tick(self, tick: Tick) -> None:
        pass

    def on_transaction(self, trade: Trade) -> None:
        pass

    def on_deinit(self) -> None:
        pass
