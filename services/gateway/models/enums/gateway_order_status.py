# Code reviewed on 2025-11-19 by pedrocarvajal

from enum import Enum, unique


@unique
class GatewayOrderStatus(Enum):
    """
    Represents the status of an order from a gateway/exchange.

    This enum standardizes order status values across different gateway
    implementations, providing a consistent interface for order state
    management.

    Values:
        CANCELLED: Order was cancelled before execution.
        EXECUTED: Order was successfully executed/filled.
        PENDING: Order is pending execution or awaiting confirmation.
    """

    CANCELLED = "cancelled"
    EXECUTED = "executed"
    PENDING = "pending"
