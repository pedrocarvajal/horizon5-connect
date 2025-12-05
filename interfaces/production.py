"""Production interface for live trading execution."""

from abc import ABC, abstractmethod


class ProductionInterface(ABC):
    """Interface defining the contract for production trading services."""

    @abstractmethod
    def run(self) -> None:
        """Start live trading execution with stream connections."""
        pass

    @abstractmethod
    def setup(self) -> None:
        """Configure production service and load portfolio."""
        pass
