from enum import Enum


class OrderStatus(Enum):
    OPENING = "opening"
    OPEN = "open"
    CLOSING = "closing"
    CLOSED = "closed"
    CANCELLED = "cancelled"
