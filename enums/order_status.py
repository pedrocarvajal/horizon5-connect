# Code reviewed on 2025-11-19 by pedrocarvajal

from enum import Enum, unique


@unique
class OrderStatus(Enum):
    """
    Represents the possible states of an order in the trading system.

    Orders progress through a lifecycle: OPENING -> OPEN -> CLOSING -> CLOSED.
    CANCELLED can occur at any point before CLOSED.

    Values:
        OPENING: Order is being initialized and prepared for execution.
        OPEN: Order is active and open in the market.
        CLOSING: Order is in the process of being closed.
        CLOSED: Order has been successfully closed and finalized.
        CANCELLED: Order was cancelled before completion.
    """

    OPENING = "opening"
    OPEN = "open"
    CLOSING = "closing"
    CLOSED = "closed"
    CANCELLED = "cancelled"
