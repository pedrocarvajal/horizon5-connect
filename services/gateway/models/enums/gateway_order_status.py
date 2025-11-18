from enum import Enum


class GatewayOrderStatus(Enum):
    PENDING = "pending"
    EXECUTED = "executed"
    CANCELLED = "cancelled"

