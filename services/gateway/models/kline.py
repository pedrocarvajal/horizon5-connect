from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class KlineModel(BaseModel):
    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    model_config = ConfigDict(arbitrary_types_allowed=True, str_strip_whitespace=True)

    source: str = Field(
        default="",
        description="The source of the data, like binance",
    )
    symbol: str = Field(
        default="",
        description="The symbol of the asset, like BTCUSDT",
    )
    open_time: int = Field(
        default=0,
        description="Opening time of the candle in unix timestamp seconds, like 1704067200",
    )
    open_price: float = Field(
        default=0.0,
        description="Opening price of the candle, like 42350.50",
    )
    high_price: float = Field(
        default=0.0,
        description="Highest price during the candle period, like 42500.00",
    )
    low_price: float = Field(
        default=0.0,
        description="Lowest price during the candle period, like 42300.00",
    )
    close_price: float = Field(
        default=0.0,
        description="Closing price of the candle, like 42450.75",
    )
    volume: float = Field(
        default=0.0,
        description="Trading volume in base asset, like 150.5 BTC",
    )
    close_time: int = Field(
        default=0,
        description="Closing time of the candle in unix timestamp seconds, like 1704153600",
    )
    quote_asset_volume: float = Field(
        default=0.0,
        description="Trading volume in quote asset, like 6380000.00 USDT",
    )
    number_of_trades: int = Field(
        default=0,
        description="Number of trades executed during the period, like 1500",
    )
    taker_buy_base_asset_volume: float = Field(
        default=0.0,
        description="Taker buy volume in base asset, like 75.2 BTC",
    )
    taker_buy_quote_asset_volume: float = Field(
        default=0.0,
        description="Taker buy volume in quote asset, like 3190000.00 USDT",
    )

    response: Any = Field(
        default=None,
        description="Raw broker-specific data for additional information",
    )

    # ───────────────────────────────────────────────────────────
    # VALIDATORS
    # ───────────────────────────────────────────────────────────
    @field_validator(
        "open_time",
        "close_time",
        "number_of_trades",
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
        "open_price",
        "high_price",
        "low_price",
        "close_price",
        "volume",
        "quote_asset_volume",
        "taker_buy_base_asset_volume",
        "taker_buy_quote_asset_volume",
        mode="before",
    )
    @classmethod
    def parse_float(cls, value: Any) -> float:
        if value is None:
            return 0.0

        if isinstance(value, float):
            return value

        if isinstance(value, (str, int)):
            return float(value)

        return 0.0
