"""Candle data model with OHLC prices and indicator data."""

import datetime
from typing import Any, Dict

from pydantic import BaseModel, Field


class CandleModel(BaseModel):
    """OHLC candlestick with open/close times and indicator data.

    Attributes:
        open_time: Candle open timestamp.
        close_time: Candle close timestamp.
        open_price: Opening price.
        high_price: Highest price during candle.
        low_price: Lowest price during candle.
        close_price: Closing price.
        indicators: Dictionary of attached indicator values.
    """

    open_time: datetime.datetime
    close_time: datetime.datetime
    open_price: float = Field(default=0.0, ge=0)
    high_price: float = Field(default=0.0, ge=0)
    low_price: float = Field(default=0.0, ge=0)
    close_price: float = Field(default=0.0, ge=0)
    indicators: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert candle to dictionary representation.

        Returns:
            Dictionary with all candle fields.
        """
        return self.model_dump()

    def to_json(self) -> str:
        """Convert candle to JSON string.

        Returns:
            JSON string representation.
        """
        return self.model_dump_json()
