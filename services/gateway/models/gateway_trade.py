# Code reviewed on 2025-11-19 by pedrocarvajal

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from enums.order_side import OrderSide


class GatewayTradeModel(BaseModel):
    """
    Model representing a trade execution from a gateway/exchange.

    This model stores trade execution details including price, volume, commission,
    and associated order information. It captures both standardized trade data
    and raw gateway-specific response data for additional information.

    Attributes:
        id: Trade ID from the gateway/exchange.
        order_id: Order ID that this trade belongs to.
        symbol: The symbol of the asset (e.g., "BTCUSDT").
        side: Trade side: BUY or SELL.
        price: Trade execution price.
        volume: Trade volume.
        commission: Commission paid for this trade.
        commission_asset: Asset used for commission.
        timestamp: Trade execution timestamp in milliseconds.
        response: Raw gateway-specific response data.
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
        description="Trade ID from the gateway/exchange",
    )
    order_id: str = Field(
        default="",
        description="Order ID that this trade belongs to",
    )
    symbol: str = Field(
        default="",
        description="The symbol of the asset, like BTCUSDT",
    )
    side: Optional[OrderSide] = Field(
        default=None,
        description="Trade side: BUY or SELL",
    )
    price: float = Field(
        default=0.0,
        ge=0,
        description="Trade execution price",
    )
    volume: float = Field(
        default=0.0,
        ge=0,
        description="Trade volume",
    )
    commission: float = Field(
        default=0.0,
        ge=0,
        description="Commission paid for this trade",
    )
    commission_asset: str = Field(
        default="",
        description="Asset used for commission",
    )
    timestamp: Optional[int] = Field(
        default=None,
        description="Trade execution timestamp in milliseconds",
    )
    response: Any = Field(
        default=None,
        description="Raw gateway-specific response data",
    )
