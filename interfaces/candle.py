"""Candle service interface for candlestick management."""

from abc import ABC, abstractmethod

from models.tick import TickModel


class CandleInterface(ABC):
    """Abstract interface (see implementations for details)."""

    @abstractmethod
    def on_tick(self, tick: TickModel) -> None:
        """Abstract method."""
        pass
