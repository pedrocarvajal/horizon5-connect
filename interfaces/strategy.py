from models.order import OrderModel
from models.tick import TickModel


class StrategyInterface:
    _enabled: bool
    _name: str

    def setup(self) -> None:
        pass

    def on_tick(self, tick: TickModel) -> None:
        pass

    def on_transaction(self, order: OrderModel) -> None:
        pass

    def on_end(self) -> None:
        pass
