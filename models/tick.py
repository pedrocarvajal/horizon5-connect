import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class TickModel(BaseModel):
    price: float = Field(default=0.0, ge=0)
    date: Optional[datetime.datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

    def to_json(self) -> str:
        return self.model_dump_json()
