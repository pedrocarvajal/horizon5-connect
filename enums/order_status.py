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

    def is_opening(self) -> bool:
        """
        Check if the order status is opening.

        Returns:
            bool: True if order status is OPENING, False otherwise.
        """
        return self == OrderStatus.OPENING

    def is_open(self) -> bool:
        """
        Check if the order status is open.

        Returns:
            bool: True if order status is OPEN, False otherwise.
        """
        return self == OrderStatus.OPEN

    def is_closing(self) -> bool:
        """
        Check if the order status is closing.

        Returns:
            bool: True if order status is CLOSING, False otherwise.
        """
        return self == OrderStatus.CLOSING

    def is_closed(self) -> bool:
        """
        Check if the order status is closed.

        Returns:
            bool: True if order status is CLOSED, False otherwise.
        """
        return self == OrderStatus.CLOSED

    def is_cancelled(self) -> bool:
        """
        Check if the order status is cancelled.

        Returns:
            bool: True if order status is CANCELLED, False otherwise.
        """
        return self == OrderStatus.CANCELLED
