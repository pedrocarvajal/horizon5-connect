from models.tick import TickModel
from models.trade import TradeModel


class StrategyInterface:
    _enabled: bool
    _name: str

    def setup(self) -> None:
        pass

    def on_tick(self, tick: TickModel) -> None:
        pass

    def on_transaction(self, trade: TradeModel) -> None:
        pass

    def on_end(self) -> None:
        pass
