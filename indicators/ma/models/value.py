import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel


class MAValueModel(BaseModel):
    date: Optional[datetime.datetime] = None
    value: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "date": self.date,
            "value": self.value,
        }
