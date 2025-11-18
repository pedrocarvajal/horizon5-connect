from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from enums.order_side import OrderSide


class GatewayPositionModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, str_strip_whitespace=True)

    symbol: str = Field(
        default="",
        description="The symbol of the asset, like BTCUSDT",
    )
    side: Optional[OrderSide] = Field(
        default=None,
        description="Position side: LONG or SHORT",
    )
    quantity: float = Field(
        default=0.0,
        description="Position quantity (positive for LONG, negative for SHORT)",
    )
    entry_price: float = Field(
        default=0.0,
        ge=0,
        description="Average entry price",
    )
    mark_price: float = Field(
        default=0.0,
        ge=0,
        description="Current mark price",
    )
    liquidation_price: float = Field(
        default=0.0,
        ge=0,
        description="Liquidation price",
    )
    leverage: int = Field(
        default=1,
        ge=1,
        description="Leverage used",
    )
    margin: float = Field(
        default=0.0,
        ge=0,
        description="Position margin",
    )
    unrealized_pnl: float = Field(
        default=0.0,
        description="Unrealized profit and loss",
    )
    percentage: float = Field(
        default=0.0,
        description="Position percentage of account",
    )
    response: Any = Field(
        default=None,
        description="Raw gateway-specific response data",
    )
