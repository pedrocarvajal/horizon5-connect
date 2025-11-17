# Last coding review: 2025-11-17 16:47:10
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from services.gateway.helpers.parse_percentage import parse_percentage as parse_percentage_helper


class GatewayTradingFeesModel(BaseModel):
    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    model_config = ConfigDict(arbitrary_types_allowed=True, str_strip_whitespace=True)

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
        return parse_percentage_helper(value=value)
