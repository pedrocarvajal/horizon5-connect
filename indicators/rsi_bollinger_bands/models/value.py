"""RSI Bollinger Bands value model for storing indicator calculations."""

import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel


class RSIBollingerBandsValueModel(BaseModel):
    """Data model representing RSI Bollinger Bands calculation result."""

    date: Optional[datetime.datetime] = None
    rsi_value: float = 0.0
    upper_band: float = 0.0
    middle_band: float = 0.0
    lower_band: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert the value model to dictionary representation."""
        return self.model_dump()

    def to_json(self) -> str:
        """Convert the value model to JSON string representation."""
        return self.model_dump_json()
