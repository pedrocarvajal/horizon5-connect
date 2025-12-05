"""Volatility value model for storing indicator calculations."""

import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class VolatilityValueModel(BaseModel):
    """Data model representing a single volatility calculation result."""

    date: Optional[datetime.datetime] = Field(default=None)
    value: float = Field(default=0.0)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the value model to dictionary representation."""
        return self.model_dump()
