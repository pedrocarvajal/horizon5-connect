# Code reviewed on 2025-11-19 by pedrocarvajal

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from enums.order_side import OrderSide


class GatewayPositionModel(BaseModel):
    """
    Model representing a trading position from a gateway/exchange.

    This model stores position information including symbol, side (LONG/SHORT),
    volume, entry price, and unrealized profit/loss. It captures both
    standardized position data and raw gateway-specific response data for
    additional information.

    Attributes:
        symbol: The symbol of the asset (e.g., "BTCUSDT").
        side: Position side: LONG (BUY) or SHORT (SELL). None if position
            is closed or side is not specified.
        volume: Position volume. Positive for LONG positions, negative for
            SHORT positions. Zero indicates no position.
        open_price: Average entry price for the position. Must be >= 0.
        unrealized_pnl: Unrealized profit and loss for the position.
        response: Raw gateway-specific response data for additional information.
    """

    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        str_strip_whitespace=True,
    )

    symbol: str = Field(
        default="",
        description="The symbol of the asset, like BTCUSDT",
    )
    side: Optional[OrderSide] = Field(
        default=None,
        description="Position side: LONG or SHORT",
    )
    volume: float = Field(
        default=0.0,
        description="Position volume (positive for LONG, negative for SHORT)",
    )
    open_price: float = Field(
        default=0.0,
        ge=0,
        description="Average entry price",
    )
    unrealized_pnl: float = Field(
        default=0.0,
        description="Unrealized profit and loss",
    )
    response: Any = Field(
        default=None,
        description="Raw gateway-specific response data",
    )
