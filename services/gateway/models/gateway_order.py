# Last coding review: 2025-11-17 16:47:10
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from enums.order_side import OrderSide
from enums.order_status import OrderStatus
from enums.order_type import OrderType


class GatewayOrderModel(BaseModel):
    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    model_config = ConfigDict(arbitrary_types_allowed=True, str_strip_whitespace=True)

    id: str = Field(
        default="",
        description="Order ID from the gateway/exchange",
    )
    symbol: str = Field(
        default="",
        description="The symbol of the asset, like BTCUSDT",
    )
    side: Optional[OrderSide] = Field(
        default=None,
        description="Order side: BUY or SELL",
    )
    order_type: Optional[OrderType] = Field(
        default=OrderType.MARKET,
        description="Order type: MARKET, LIMIT, etc.",
    )
    status: Optional[OrderStatus] = Field(
        default=OrderStatus.OPENING,
        description="Order status: OPENING, OPENED, CLOSED, etc.",
    )
    volume: float = Field(
        default=0.0,
        ge=0,
        description="Original order quantity",
    )
    executed_volume: float = Field(
        default=0.0,
        ge=0,
        description="Executed order quantity",
    )
    price: float = Field(
        default=0.0,
        ge=0,
        description="Order price",
    )
    response: Any = Field(
        default=None,
        description="Raw gateway-specific response data",
    )
