from abc import ABC, abstractmethod

from models.tick import TickModel


class IndicatorInterface(ABC):
    @abstractmethod
    def on_tick(self, tick: TickModel) -> None:
        pass

    def on_end(self) -> None:
        pass
