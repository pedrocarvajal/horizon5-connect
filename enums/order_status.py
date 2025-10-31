from enum import Enum


class OrderStatus(Enum):
    ORDER_CREATED = "order_created"
    ORDER_UPDATED = "order_updated"
    ORDER_CANCELLED = "order_cancelled"
    ORDER_FILLED = "order_filled"
    ORDER_PARTIALLY_FILLED = "order_partially_filled"
    ORDER_REJECTED = "order_rejected"
    ORDER_EXPIRED = "order_expired"
    ORDER_CANCELLED_BY_USER = "order_cancelled_by_user"
    ORDER_CANCELLED_BY_SYSTEM = "order_cancelled_by_system"
    ORDER_CANCELLED_BY_EXPIRATION = "order_cancelled_by_expiration"
    ORDER_CANCELLED_BY_LIQUIDATION = "order_cancelled_by_liquidation"
