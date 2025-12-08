"""ADX value model for storing indicator calculations."""

import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel


class ADXValueModel(BaseModel):
    """Data model representing a single ADX calculation result."""

    date: Optional[datetime.datetime] = None
    adx: float = 0.0
    plus_di: float = 0.0
    minus_di: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert the value model to dictionary representation."""
        return self.model_dump()

    def to_json(self) -> str:
        """Convert the value model to JSON string representation."""
        return self.model_dump_json()
