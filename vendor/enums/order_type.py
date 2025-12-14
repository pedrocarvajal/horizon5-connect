"""Order type enumeration (MARKET, LIMIT, etc)."""

from enum import Enum, unique


@unique
class OrderType(Enum):
    """Represents the different types of orders available in the trading system."""

    MARKET = "market"

    def is_market(self) -> bool:
        """
        Check if the order type is market.

        Returns:
            bool: True if order type is MARKET, False otherwise.
        """
        return self == OrderType.MARKET
