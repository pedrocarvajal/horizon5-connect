from models.tick import TickModel


class IndicatorInterface:
    def on_tick(self, tick: TickModel) -> None:
        pass

    def on_end(self) -> None:
        pass
