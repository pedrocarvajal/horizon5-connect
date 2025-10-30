from typing import Any

from models.tick import TickModel


class IndicatorInterface:
    _name: str
    _elements: list[dict[str, Any]]

    def on_tick(self, tick: TickModel) -> None:
        pass

    def on_end(self) -> None:
        pass

    def get(self, index: int) -> dict[str, Any] | None:
        if len(self._elements) == 0 or abs(index) > len(self._elements):
            return None

        return self._elements[index]

    @property
    def name(self) -> str:
        return self._name
