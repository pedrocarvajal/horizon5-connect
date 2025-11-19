# Code reviewed on 2025-11-19 by pedrocarvajal

from enum import Enum, unique


@unique
class OrderSide(str, Enum):
    """
    Represents the side of an order (buy or sell).

    This enum is used throughout the trading system to indicate whether an order
    is a buy order or a sell order. Values are lowercase strings for API
    compatibility with trading gateways.

    Inherits from str to allow direct string operations and JSON serialization.
    """

    BUY = "buy"
    SELL = "sell"

    def is_buy(self) -> bool:
        """
        Check if the order side is buy.

        Returns:
            bool: True if order side is BUY, False otherwise.
        """
        return self == OrderSide.BUY

    def is_sell(self) -> bool:
        """
        Check if the order side is sell.

        Returns:
            bool: True if order side is SELL, False otherwise.
        """
        return self == OrderSide.SELL
