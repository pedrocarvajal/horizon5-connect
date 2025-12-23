"""Order sync result model for gateway synchronization responses."""

from pydantic import BaseModel, Field

from vendor.enums.order_status import OrderStatus


class OrderSyncResult(BaseModel):
    """Result of synchronizing an order with the gateway.

    Contains the current state of an order as reported by the gateway,
    including whether the position still exists, current prices, and
    realized profit/loss for closed positions.

    Attributes:
        exists: Whether the position exists in the gateway.
        status: Current order status from gateway perspective.
        close_price: Close price if order was closed (0.0 if still open).
        profit: Realized profit/loss if closed (0.0 if still open).
        executed_volume: Volume that was executed.
        current_price: Current market price of the position.
    """

    exists: bool = Field(
        description="Whether the position exists in the gateway",
    )
    status: OrderStatus = Field(
        description="Current order status from gateway",
    )
    close_price: float = Field(
        default=0.0,
        ge=0,
        description="Close price if order was closed",
    )
    profit: float = Field(
        default=0.0,
        description="Realized profit/loss if closed",
    )
    executed_volume: float = Field(
        default=0.0,
        ge=0,
        description="Volume that was executed",
    )
    current_price: float = Field(
        default=0.0,
        ge=0,
        description="Current market price of the position",
    )
