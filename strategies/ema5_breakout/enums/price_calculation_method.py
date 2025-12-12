"""Price calculation method enumeration."""

from enum import Enum, unique


@unique
class PriceCalculationMethod(str, Enum):
    """Price calculation method for stop loss and take profit levels.

    Attributes:
        PERCENTAGE: Use percentage-based price calculation.
        ATR: Use Average True Range for price calculation.
    """

    PERCENTAGE = "percentage"
    ATR = "atr"

    def is_percentage(self) -> bool:
        """Check if method is PERCENTAGE."""
        return self == PriceCalculationMethod.PERCENTAGE

    def is_atr(self) -> bool:
        """Check if method is ATR."""
        return self == PriceCalculationMethod.ATR
