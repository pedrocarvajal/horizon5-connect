# Last coding review: 2025-11-17 16:47:10
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from helpers.parse import (
    parse_int as parse_int_helper,
    parse_optional_float as parse_optional_float_helper,
    parse_percentage as parse_percentage_helper,
)


class GatewaySymbolInfoModel(BaseModel):
    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    model_config = ConfigDict(arbitrary_types_allowed=True, str_strip_whitespace=True)

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
        return parse_optional_float_helper(value=value)

    @field_validator(
        "margin_percent",
        mode="before",
    )
    @classmethod
    def parse_percentage(cls, value: Any) -> Optional[float]:
        return parse_percentage_helper(value=value)
