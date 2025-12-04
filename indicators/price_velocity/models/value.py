"""Price Velocity value model for storing indicator calculations."""

import datetime
from typing import Any, Dict, Optional


class PriceVelocityValueModel:
    """Data model representing a single price velocity calculation result."""

    date: Optional[datetime.datetime] = None
    value: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert the value model to dictionary representation."""
        return {
            "date": self.date,
            "value": self.value,
        }
