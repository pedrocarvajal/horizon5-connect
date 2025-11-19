# Code reviewed on 2025-11-19 by pedrocarvajal

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from helpers.parse import (
    parse_int as parse_int_helper,
)
from helpers.parse import (
    parse_optional_float as parse_optional_float_helper,
)
from helpers.parse import (
    parse_percentage as parse_percentage_helper,
)


class GatewaySymbolInfoModel(BaseModel):
    """
    Model representing symbol trading information from a gateway/exchange.

    This model stores comprehensive trading specifications for a symbol including
    price and quantity precision, min/max constraints, tick/step sizes, margin
    requirements, and trading status. It captures both standardized symbol data
    and raw gateway-specific response data for additional information.

    Attributes:
        symbol: The symbol of the asset (e.g., "BTCUSDT").
        base_asset: The base asset being traded (e.g., "BTC" in BTCUSDT).
        quote_asset: The quote asset used for pricing (e.g., "USDT" in BTCUSDT).
        price_precision: Number of decimal places for price (e.g., 2 for $100.50).
        quantity_precision: Number of decimal places for quantity (e.g., 3 for 0.001 BTC).
        min_price: Minimum allowed price (e.g., 0.01).
        max_price: Maximum allowed price (e.g., 1000000.00).
        tick_size: Minimum price increment (e.g., 0.10).
        min_quantity: Minimum order quantity (e.g., 0.001 BTC).
        max_quantity: Maximum order quantity (e.g., 1000 BTC).
        step_size: Minimum quantity increment (e.g., 0.001).
        min_notional: Minimum order value in quote asset (e.g., 100 USDT minimum per order).
        status: Trading status of the symbol (e.g., "TRADING" or "SUSPENDED").
        margin_percent: Required margin percentage for leveraged trading (e.g., 5.0 for 5%).
        response: Raw broker-specific data for additional information.
    """

    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        str_strip_whitespace=True,
    )

    symbol: str = Field(
        default="",
        description="The symbol of the asset, like BTCUSDT",
    )
    base_asset: str = Field(
        default="",
        description="The base asset being traded, like BTC in BTCUSDT",
    )
    quote_asset: str = Field(
        default="",
        description="The quote asset used for pricing, like USDT in BTCUSDT",
    )
    price_precision: int = Field(
        default=2,
        description="Number of decimal places for price, like 2 for $100.50",
    )
    quantity_precision: int = Field(
        default=2,
        description="Number of decimal places for quantity, like 3 for 0.001 BTC",
    )
    min_price: Optional[float] = Field(
        default=None,
        description="Minimum allowed price, like 0.01",
    )
    max_price: Optional[float] = Field(
        default=None,
        description="Maximum allowed price, like 1000000.00",
    )
    tick_size: Optional[float] = Field(
        default=None,
        description="Minimum price increment, like 0.10",
    )
    min_quantity: Optional[float] = Field(
        default=None,
        description="Minimum order quantity, like 0.001 BTC",
    )
    max_quantity: Optional[float] = Field(
        default=None,
        description="Maximum order quantity, like 1000 BTC",
    )
    step_size: Optional[float] = Field(
        default=None,
        description="Minimum quantity increment, like 0.001",
    )
    min_notional: Optional[float] = Field(
        default=None,
        description="Minimum order value in quote asset, like 100 USDT minimum per order",
    )
    status: str = Field(
        default="TRADING",
        description="Trading status of the symbol, like TRADING or SUSPENDED",
    )
    margin_percent: Optional[float] = Field(
        default=None,
        description="Required margin percentage for leveraged trading, like 5.0 for 5%",
    )
    response: Any = Field(
        default=None,
        description="Raw broker-specific data for additional information",
    )

    # ───────────────────────────────────────────────────────────
    # PRIVATE METHODS
    # ───────────────────────────────────────────────────────────
    @field_validator(
        "price_precision",
        "quantity_precision",
        mode="before",
    )
    @classmethod
    def parse_int(cls, value: Any) -> int:
        """
        Parse and convert value to integer for precision fields.

        Converts various input formats (string, int, float) to an integer.
        Returns 0 if conversion fails.

        Args:
            value: The value to parse. Can be None, empty string, float, int,
                or string representation of a number.

        Returns:
            int: The parsed integer value, or 0 if conversion fails.

        Example:
            >>> GatewaySymbolInfoModel.parse_int("2")
            2
            >>> GatewaySymbolInfoModel.parse_int(3.5)
            3
            >>> GatewaySymbolInfoModel.parse_int(None)
            0
        """
        return parse_int_helper(value=value)

    @field_validator(
        "min_price",
        "max_price",
        "tick_size",
        "min_quantity",
        "max_quantity",
        "step_size",
        "min_notional",
        mode="before",
    )
    @classmethod
    def parse_float(cls, value: Any) -> Optional[float]:
        """
        Parse and convert value to float for price and quantity constraint fields.

        Converts various input formats (string, int, float) to a float.
        Returns None if value is None or empty string.

        Args:
            value: The value to parse. Can be None, empty string, float, int,
                or string representation of a number.

        Returns:
            Optional[float]: The parsed float value, or None if value is None
                or empty string.

        Example:
            >>> GatewaySymbolInfoModel.parse_float("0.01")
            0.01
            >>> GatewaySymbolInfoModel.parse_float(100)
            100.0
            >>> GatewaySymbolInfoModel.parse_float(None)
            None
        """
        return parse_optional_float_helper(value=value)

    @field_validator(
        "margin_percent",
        mode="before",
    )
    @classmethod
    def parse_percentage(cls, value: Any) -> Optional[float]:
        """
        Parse and normalize percentage values for margin percentage field.

        Converts various input formats (string, int, float) to a decimal
        representation. If the value is greater than 1, it assumes the value
        is a percentage and divides by 100 to convert to decimal.

        Args:
            value: The percentage value to parse. Can be None, empty string,
                float, int, or string representation of a number.

        Returns:
            Optional[float]: The parsed percentage as a decimal (e.g., 0.05
                for 5%), or None if value is None or empty string.

        Example:
            >>> GatewaySymbolInfoModel.parse_percentage("5")
            0.05
            >>> GatewaySymbolInfoModel.parse_percentage(5.0)
            0.05
            >>> GatewaySymbolInfoModel.parse_percentage(0.05)
            0.05
            >>> GatewaySymbolInfoModel.parse_percentage(None)
            None
        """
        return parse_percentage_helper(value=value)
