"""Take profit and stop loss calculation method enum."""

from enum import Enum


class TpSlMethod(str, Enum):
    """Enumeration of available methods for calculating take profit and stop loss prices.

    PERCENTAGE: Calculate as a percentage of the entry price.
        Example: entry=100, tp_value=0.05 -> tp_price=105

    ATR: Calculate using ATR (Average True Range) multiplier.
        Example: entry=100, atr=2.5, tp_value=2.0 -> tp_price=105

    FIXED: Calculate as a fixed amount added/subtracted from entry price.
        Example: entry=100, tp_value=10 -> tp_price=110
    """

    PERCENTAGE = "percentage"
    ATR = "atr"
    FIXED = "fixed"
