from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SymbolInfoModel(BaseModel):
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
    # VALIDATORS
    # ───────────────────────────────────────────────────────────
    @field_validator(
        "price_precision",
        "quantity_precision",
        mode="before",
    )
    @classmethod
    def parse_int(cls, value: Any) -> int:
        if value is None:
            return 0

        if isinstance(value, int):
            return value

        if isinstance(value, str):
            return int(float(value))

        return int(value)

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
        if value is None or value == "":
            return None

        if isinstance(value, float):
            return value

        if isinstance(value, (str, int)):
            return float(value)

        return None

    @field_validator(
        "margin_percent",
        mode="before",
    )
    @classmethod
    def parse_percentage(cls, value: Any) -> Optional[float]:
        parsed_value = None

        if value is None or value == "":
            return None

        if isinstance(value, float):
            parsed_value = value

        elif isinstance(value, (str, int)):
            parsed_value = float(value)

        if parsed_value is not None and parsed_value > 1:
            return parsed_value / 100

        return parsed_value
