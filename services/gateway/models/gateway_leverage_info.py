# Last coding review: 2025-11-18 12:40:00
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from services.gateway.helpers.parse_int import parse_int as parse_int_helper


class GatewayLeverageInfoModel(BaseModel):
    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    model_config = ConfigDict(arbitrary_types_allowed=True, str_strip_whitespace=True)

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
        return parse_int_helper(value=value)
