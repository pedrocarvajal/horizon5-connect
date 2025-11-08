from abc import ABC, abstractmethod
from typing import Any, List

from models.tick import TickModel


class IndicatorInterface(ABC):
    @abstractmethod
    def on_tick(self, tick: TickModel) -> None:
        pass

    def on_end(self) -> None:
        pass

    @property
    def key(self) -> str:
        return self._key

    @property
    def values(self) -> List[Any]:
        return self._values
