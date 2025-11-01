import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class TradeModel(BaseModel):
    id: int = Field(default=0, ge=0)
    order_id: int = Field(default=0, ge=0)
    symbol: str = ""
    price: float = Field(default=0.0, ge=0)
    volume: float = Field(default=0.0, ge=0)
    is_buyer: bool = False
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

    def to_json(self) -> str:
        return self.model_dump_json()
