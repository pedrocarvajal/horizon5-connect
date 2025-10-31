from enum import Enum


class OrderEvent(Enum):
    OPEN_ORDER = "open_order"
    CLOSE_ORDER = "close_order"
