"""Candle service interface for candlestick management."""

from abc import ABC, abstractmethod
from typing import List

from models.candle import CandleModel
from models.tick import TickModel


class CandleInterface(ABC):
    """Abstract interface (see implementations for details)."""

    _candles: List[CandleModel]

    @abstractmethod
    def on_tick(self, tick: TickModel) -> None:
        """Abstract method."""
        pass

    @property
    @abstractmethod
    def candles(self) -> List[CandleModel]:
        """Abstract property."""
        pass
