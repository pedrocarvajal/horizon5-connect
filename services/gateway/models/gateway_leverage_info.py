# Code reviewed on 2025-11-19 by pedrocarvajal

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from helpers.parse import parse_int as parse_int_helper


class GatewayLeverageInfoModel(BaseModel):
    """
    Model representing leverage information for a symbol from a gateway/exchange.

    This model stores leverage information including the symbol and maximum
    available leverage. It captures both standardized leverage data and raw
    gateway-specific response data for additional information.

    Attributes:
        symbol: The symbol of the asset (e.g., "BTCUSDT").
        leverage: Maximum available leverage for the symbol. Must be >= 1.
            Defaults to 1 (no leverage).
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
    leverage: int = Field(
        default=1,
        ge=1,
        description="Maximum available leverage for the symbol",
    )
    response: Any = Field(
        default=None,
        description="Raw broker-specific data for additional information",
    )

    # ───────────────────────────────────────────────────────────
    # PRIVATE METHODS
    # ───────────────────────────────────────────────────────────
    @field_validator(
        "leverage",
        mode="before",
    )
    @classmethod
    def parse_int(cls, value: Any) -> int:
        """
        Parse and convert value to integer for leverage field.

        Converts various input formats (string, int, float) to an integer.
        Returns 0 if conversion fails.

        Args:
            value: The value to parse. Can be None, empty string, float, int,
                or string representation of a number.

        Returns:
            int: The parsed integer value, or 0 if conversion fails.

        Example:
            >>> GatewayLeverageInfoModel.parse_int("20")
            20
            >>> GatewayLeverageInfoModel.parse_int(10.5)
            10
            >>> GatewayLeverageInfoModel.parse_int(None)
            0
        """
        return parse_int_helper(value=value)
