"""Ticks interface defining the contract for tick data services."""

import datetime
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Iterator, List, Tuple

import polars

from vendor.models.tick import TickModel


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

    @abstractmethod
    def get_timeline(
        self,
        from_date: datetime.datetime,
        to_date: datetime.datetime,
    ) -> List[int]:
        """Generate timeline of timestamps from from_date to to_date."""

    @abstractmethod
    def load_assets_data(
        self,
        symbols: List[str],
        from_date: datetime.datetime,
        to_date: datetime.datetime,
    ) -> Dict[str, polars.DataFrame]:
        """Load parquet data for multiple assets into memory."""

    @abstractmethod
    def iterate_ticks(
        self,
        symbols: List[str],
        from_date: datetime.datetime,
        to_date: datetime.datetime,
    ) -> Iterator[Tuple[datetime.datetime, Dict[str, TickModel]]]:
        """Iterate over timeline yielding ticks for each timestamp."""

    @property
    def folder(self) -> Path:
        """Return the folder path for tick data storage."""
        return self._ticks_folder
