# Code reviewed on 2025-11-19 by pedrocarvajal

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from helpers.parse import parse_percentage as parse_percentage_helper


class GatewayTradingFeesModel(BaseModel):
    """
    Model representing trading fees for a gateway/exchange symbol.

    This model stores maker and taker commission rates for a specific trading
    symbol, along with raw broker-specific response data for additional
    information.

    Attributes:
        symbol: The trading symbol (e.g., "BTCUSDT").
        maker_commission: Maker commission rate as decimal (e.g., 0.001 for 0.1%).
        taker_commission: Taker commission rate as decimal (e.g., 0.001 for 0.1%).
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
    maker_commission: Optional[float] = Field(
        default=None,
        description="Maker commission rate as decimal, like 0.001 for 0.1%",
    )
    taker_commission: Optional[float] = Field(
        default=None,
        description="Taker commission rate as decimal, like 0.001 for 0.1%",
    )
    response: Any = Field(
        default=None,
        description="Raw broker-specific data for additional information",
    )

    # ───────────────────────────────────────────────────────────
    # PRIVATE METHODS
    # ───────────────────────────────────────────────────────────
    @field_validator(
        "maker_commission",
        "taker_commission",
        mode="before",
    )
    @classmethod
    def parse_percentage(cls, value: Any) -> Optional[float]:
        """
        Parse and normalize percentage values for commission fields.

        Converts various input formats (string, int, float) to a decimal
        representation. If the value is greater than 1, it assumes the value
        is a percentage and divides by 100 to convert to decimal.

        Args:
            value: The percentage value to parse. Can be None, empty string,
                float, int, or string representation of a number.

        Returns:
            Optional[float]: The parsed percentage as a decimal (e.g., 0.001
                for 0.1%), or None if value is None or empty string.

        Example:
            >>> GatewayTradingFeesModel.parse_percentage("0.1")
            0.1
            >>> GatewayTradingFeesModel.parse_percentage(10)
            0.1
            >>> GatewayTradingFeesModel.parse_percentage(None)
            None
        """
        return parse_percentage_helper(value=value)
