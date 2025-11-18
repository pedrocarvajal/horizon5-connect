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
