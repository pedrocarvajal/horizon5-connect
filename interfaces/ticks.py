"""Ticks interface defining the contract for tick data services."""

import datetime
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, List

from models.tick import TickModel


class TicksInterface(ABC):
    """Interface defining the contract for tick data services."""

    _ticks_folder: Path

    @abstractmethod
    def setup(self, **kwargs: Any) -> None:
        """Configure the ticks service with required parameters."""

    @abstractmethod
    def ticks(
        self,
        from_date: datetime.datetime,
        to_date: datetime.datetime,
    ) -> List[TickModel]:
        """Retrieve tick data for the specified date range."""

    @property
    def folder(self) -> Path:
        """Return the folder path for tick data storage."""
        return self._ticks_folder
