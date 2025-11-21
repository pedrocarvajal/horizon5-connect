import datetime
from typing import Any, Dict

from pydantic import BaseModel, Field


class TickModel(BaseModel):
    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    is_simulated: bool = Field(
        default=True, description="True if tick is from backtest/simulation, False if from live production"
    )
    price: float = Field(default=0.0, ge=0)
    bid_price: float = Field(default=0.0, ge=0)
    ask_price: float = Field(default=0.0, ge=0)
    date: datetime.datetime

    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

    def to_json(self) -> str:
        return self.model_dump_json()
