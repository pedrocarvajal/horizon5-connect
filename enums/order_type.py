# Code reviewed on 2025-11-19 by pedrocarvajal

from enum import Enum, unique


@unique
class OrderType(Enum):
    """Represents the different types of orders available in the trading system."""

    MARKET = "market"
    LIMIT = "limit"

    def is_market(self) -> bool:
        """
        Check if the order type is market.

        Returns:
            bool: True if order type is MARKET, False otherwise.
        """
        return self == OrderType.MARKET

    def is_limit(self) -> bool:
        """
        Check if the order type is limit.

        Returns:
            bool: True if order type is LIMIT, False otherwise.
        """
        return self == OrderType.LIMIT

    def requires_price(self) -> bool:
        """
        Check if the order type requires a price.

        Returns:
            bool: True if order type requires price (LIMIT, STOP_LOSS_LIMIT, TAKE_PROFIT_LIMIT), False otherwise.
        """
        return self in (OrderType.LIMIT, OrderType.STOP_LOSS_LIMIT, OrderType.TAKE_PROFIT_LIMIT)
