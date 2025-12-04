"""Indicator interface for technical analysis calculations."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from models.tick import TickModel


class IndicatorInterface(ABC):
    """Abstract interface (see implementations for details)."""

    _key: str
    _values: List[Any]
    _candles: List[Dict[str, Any]]

    @abstractmethod
    def on_tick(self, tick: TickModel) -> None:
        """Abstract method."""
        pass

    def on_end(self) -> None:  # noqa: B027
        """Abstract method."""
        pass

    @property
    def key(self) -> str:
        """Abstract method (see implementations for details)."""
        return self._key

    @property
    def values(self) -> List[Any]:
        """Abstract method (see implementations for details)."""
        return self._values
