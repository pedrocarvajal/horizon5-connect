from enum import Enum


class OrderStatus(Enum):
    OPENING = "opening"
    OPENED = "opened"
    CLOSING = "closing"
    CLOSED = "closed"
    CANCELLED = "cancelled"
