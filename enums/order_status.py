from enum import Enum


class OrderStatus(Enum):
    PENDING = "pending"
    OPENED = "opened"
    CLOSED = "closed"
    CANCELLED = "cancelled"
