"""Gateway symbol info model for trading pair specifications."""

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from vendor.helpers.parse_int import parse_int as parse_int_helper
from vendor.helpers.parse_optional_float import parse_optional_float as parse_optional_float_helper


class GatewaySymbolInfoModel(BaseModel):
    """
    Model representing symbol trading information from a gateway/exchange.

    This model stores comprehensive trading specifications for a symbol based on
    MetaAPI's MetatraderSymbolSpecification. Includes price and quantity precision,
    min/max constraints, tick/step sizes, margin requirements, swap rates,
    trading sessions, and leverage information.

    Reference: https://metaapi.cloud/docs/client/models/metatraderSymbolSpecification/
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        str_strip_whitespace=True,
    )

    symbol: str = Field(
        default="",
        description="Currency pair or index identifier (e.g., XAUUSD)",
    )
    base_asset: str = Field(
        default="",
        description="Base asset of the trading pair (e.g., BTC)",
    )
    quote_asset: str = Field(
        default="",
        description="Quote asset of the trading pair (e.g., USDT)",
    )
    price_precision: int = Field(
        default=2,
        description="Number of decimal places for price",
    )
    quantity_precision: int = Field(
        default=2,
        description="Number of decimal places for quantity/volume",
    )
    min_price: Optional[float] = Field(
        default=None,
        description="Minimum allowed order price",
    )
    max_price: Optional[float] = Field(
        default=None,
        description="Maximum allowed order price",
    )
    tick_size: Optional[float] = Field(
        default=None,
        description="Minimum price movement increment",
    )
    min_notional: Optional[float] = Field(
        default=None,
        description="Minimum notional value for orders",
    )
    margin_percent: Optional[float] = Field(
        default=None,
        description="Required margin percentage for the symbol",
    )
    point: Optional[float] = Field(
        default=None,
        description="Smallest price unit value",
    )
    pip_size: Optional[float] = Field(
        default=None,
        description="Pip value for spot/CFD symbols",
    )
    min_quantity: Optional[float] = Field(
        default=None,
        description="Minimum tradeable volume (minVolume)",
    )
    max_quantity: Optional[float] = Field(
        default=None,
        description="Maximum tradeable volume (maxVolume)",
    )
    step_size: Optional[float] = Field(
        default=None,
        description="Volume increment for orders (volumeStep)",
    )
    contract_size: Optional[float] = Field(
        default=None,
        description="Lot size in base currency units",
    )
    initial_margin: Optional[float] = Field(
        default=None,
        description="Required margin for one lot",
    )
    maintenance_margin: Optional[float] = Field(
        default=None,
        description="Margin needed for position maintenance",
    )
    hedged_margin: Optional[float] = Field(
        default=None,
        description="Margin for opposing positions",
    )
    swap_mode: str = Field(
        default="POINTS",
        description="Swap calculation model",
    )
    swap_long: Optional[float] = Field(
        default=None,
        description="Long position swap rate",
    )
    swap_short: Optional[float] = Field(
        default=None,
        description="Short position swap rate",
    )
    status: str = Field(
        default="TRADING",
        description="Trading status of the symbol (TRADING, SUSPENDED)",
    )
    response: Any = Field(
        default=None,
        description="Raw broker-specific data for additional information",
    )

    @field_validator(
        "point",
        "pip_size",
        "min_price",
        "max_price",
        "tick_size",
        "min_quantity",
        "max_quantity",
        "step_size",
        "min_notional",
        "margin_percent",
        "contract_size",
        "initial_margin",
        "maintenance_margin",
        "hedged_margin",
        "swap_long",
        "swap_short",
        mode="before",
    )
    @classmethod
    def parse_float(cls, value: Any) -> Optional[float]:
        """Parse and convert value to float."""
        return parse_optional_float_helper(value=value)

    @field_validator(
        "quantity_precision",
        mode="before",
    )
    @classmethod
    def parse_int(cls, value: Any) -> int:
        """Parse and convert value to integer."""
        return parse_int_helper(value=value)
