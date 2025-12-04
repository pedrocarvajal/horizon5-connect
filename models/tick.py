"""Market tick data model with price and timestamp information."""

import datetime
from typing import Any, Dict

from pydantic import BaseModel, Field


class TickModel(BaseModel):
    """Market tick with bid/ask prices and timestamp.

    Attributes:
        is_simulated: Whether tick is from backtest or live production.
        price: Current market price.
        bid_price: Bid price.
        ask_price: Ask price.
        date: Tick timestamp.
    """

    is_simulated: bool = Field(
        default=True,
        description="True if tick is from backtest/simulation, False if from live production",
    )
    price: float = Field(default=0.0, ge=0)
    bid_price: float = Field(default=0.0, ge=0)
    ask_price: float = Field(default=0.0, ge=0)
    date: datetime.datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert tick to dictionary representation.

        Returns:
            Dictionary with all tick fields.
        """
        return self.model_dump()

    def to_json(self) -> str:
        """Convert tick to JSON string.

        Returns:
            JSON string representation.
        """
        return self.model_dump_json()
