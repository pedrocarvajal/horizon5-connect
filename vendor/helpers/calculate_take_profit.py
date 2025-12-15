"""Take profit price calculation utilities."""

from typing import Optional

from vendor.enums.order_side import OrderSide
from vendor.enums.tp_sl_method import TpSlMethod


def calculate_take_profit(
    entry_price: float,
    value: float,
    method: TpSlMethod,
    side: OrderSide,
    atr_value: Optional[float] = None,
) -> float:
    """
    Calculate take profit price based on the specified method.

    Args:
        entry_price: The entry price of the order.
        value: The take profit value (interpretation depends on method).
        method: The calculation method (PERCENTAGE, ATR, or FIXED).
        side: Order side (BUY or SELL) to determine direction.
        atr_value: Current ATR value (required when method is ATR).

    Returns:
        The calculated take profit price.

    Raises:
        ValueError: If ATR method is used but atr_value is not provided.
    """
    direction = 1 if side == OrderSide.BUY else -1

    if method == TpSlMethod.PERCENTAGE:
        return entry_price * (1 + direction * value)

    if method == TpSlMethod.ATR:
        if atr_value is None:
            raise ValueError("atr_value is required when using ATR method")
        return entry_price + (direction * value * atr_value)

    if method == TpSlMethod.FIXED:
        return entry_price + (direction * value)

    return entry_price
