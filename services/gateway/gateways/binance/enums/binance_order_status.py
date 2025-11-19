# Code reviewed on 2025-11-19 by pedrocarvajal

from enum import Enum, unique


@unique
class BinanceOrderStatus(str, Enum):
    """
    Represents order status values from the Binance API.

    This enum maps Binance exchange order status strings to standardized enum
    values. These statuses are used when processing order responses from Binance
    and converting them to the internal GatewayOrderStatus format.

    Inherits from str to allow direct string operations and JSON serialization
    for API compatibility.

    Values:
        CANCELED: Order has been canceled.
        EXPIRED: Order has expired.
        FILLED: Order has been completely filled.
        NEW: Order has been accepted by the engine.
        PARTIALLY_FILLED: Order has been partially filled.
        PENDING_CANCEL: Order is pending cancellation.
        REJECTED: Order has been rejected.
    """

    CANCELED = "CANCELED"
    EXPIRED = "EXPIRED"
    FILLED = "FILLED"
    NEW = "NEW"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    PENDING_CANCEL = "PENDING_CANCEL"
    REJECTED = "REJECTED"
