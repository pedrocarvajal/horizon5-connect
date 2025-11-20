# Code reviewed on 2025-11-19 by pedrocarvajal

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from enums.order_side import OrderSide
from enums.order_type import OrderType
from services.gateway.models.enums.gateway_order_status import GatewayOrderStatus


class GatewayOrderModel(BaseModel):
    """
    Model representing an order from a gateway/exchange.

    This model stores order information including identification, symbol, side,
    type, status, volume, execution details, and price. It captures both
    standardized order data and raw gateway-specific response data for
    additional information.

    Attributes:
        id: Order ID from the gateway/exchange.
        symbol: The symbol of the asset (e.g., "BTCUSDT").
        side: Order side: BUY or SELL. None if side is not specified.
        order_type: Order type: MARKET, LIMIT, etc. Defaults to MARKET.
        status: Order status: PENDING, EXECUTED, CANCELLED. Defaults to PENDING.
        volume: Original order quantity. Must be >= 0.
        executed_volume: Executed order quantity. Must be >= 0.
        price: Order price. Must be >= 0. For MARKET orders, this may be 0
            until execution.
        response: Raw gateway-specific response data for additional information.
    """

    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        str_strip_whitespace=True,
    )
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
    status: Optional[GatewayOrderStatus] = Field(
        default=GatewayOrderStatus.PENDING,
        description="Order status: PENDING, EXECUTED, CANCELLED",
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
