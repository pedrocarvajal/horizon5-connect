from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TradingFeesModel(BaseModel):
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
    # VALIDATORS
    # ───────────────────────────────────────────────────────────
    @field_validator(
        "maker_commission",
        "taker_commission",
        mode="before",
    )
    @classmethod
    def parse_percentage(cls, value: Any) -> Optional[float]:
        if value is None or value == "":
            return None

        parsed_value = None

        if isinstance(value, float):
            parsed_value = value

        elif isinstance(value, (str, int)):
            parsed_value = float(value)

        if parsed_value is not None and parsed_value > 1:
            return parsed_value / 100

        return parsed_value
