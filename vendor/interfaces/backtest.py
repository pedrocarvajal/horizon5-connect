"""Backtest interface for historical strategy simulation."""

from abc import ABC, abstractmethod


class BacktestInterface(ABC):
    """Interface for backtest service.

    Defines the public contract for backtest execution and lifecycle management.
    """

    @abstractmethod
    def run(self) -> None:
        """Execute backtest by processing all ticks in date range."""
        pass
