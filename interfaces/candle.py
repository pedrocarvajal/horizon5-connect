from models.tick import TickModel


class CandleInterface:
    def on_tick(self, tick: TickModel) -> None:
        pass
