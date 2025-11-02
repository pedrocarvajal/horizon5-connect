from abc import ABC, abstractmethod

from models.tick import TickModel


class CandleInterface(ABC):
    @abstractmethod
    def on_tick(self, tick: TickModel) -> None:
        pass
