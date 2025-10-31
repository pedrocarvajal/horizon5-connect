from models.tick import TickModel


class OrderbookInterface:
    def setup(self) -> None:
        pass

    def on_tick(self, tick: TickModel) -> None:
        pass

    def on_end(self) -> None:
        pass
