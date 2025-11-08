import datetime
from typing import Any, Dict, Optional


class VolatilityValueModel:
    date: Optional[datetime.datetime] = None
    value: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "date": self.date,
            "value": self.value,
        }
