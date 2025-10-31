from enum import Enum


class OrderStatus(Enum):
    ORDER_CREATED = "order_created"
    ORDER_CANCELLED = "order_cancelled"
    ORDER_FILLED = "order_filled"
    ORDER_PARTIALLY_FILLED = "order_partially_filled"
