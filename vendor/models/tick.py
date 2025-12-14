"""Market tick data model with price and timestamp information."""

import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class TickModel(BaseModel):
    """Market tick with OHLC prices and timestamp.

    Attributes:
        is_simulated: Whether tick is from backtest or live production.
        open_price: Open price from source candle (for correct OHLC aggregation).
        high_price: High price from source candle (for correct OHLC aggregation).
        low_price: Low price from source candle (for correct OHLC aggregation).
        close_price: Close price (current market price).
        bid_price: Bid price (for live trading).
        ask_price: Ask price (for live trading).
        date: Tick timestamp.
    """

    is_simulated: bool = Field(default=True, description="True if tick is from backtest/simulation")
    open_price: Optional[float] = Field(default=None, ge=0)
    high_price: Optional[float] = Field(default=None, ge=0)
    low_price: Optional[float] = Field(default=None, ge=0)
    close_price: float = Field(default=0.0, ge=0)
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
