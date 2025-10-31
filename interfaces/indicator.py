from typing import Any, List

from models.tick import TickModel


class IndicatorInterface:
    _name: str
    _values: List[Any]

    def on_tick(self, tick: TickModel) -> None:
        pass

    def on_end(self) -> None:
        pass

    @property
    def name(self) -> str:
        return self._name

    @property
    def values(self) -> List[Any]:
        return self._values
