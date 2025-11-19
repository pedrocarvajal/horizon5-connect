# Code reviewed on 2025-11-19 by pedrocarvajal

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from helpers.parse import (
    parse_float as parse_float_helper,
)
from helpers.parse import (
    parse_int as parse_int_helper,
)


class GatewayKlineModel(BaseModel):
    """
    Model representing a candlestick (kline) from a gateway/exchange.

    This model stores OHLCV (Open, High, Low, Close, Volume) data along with
    additional trading metrics including quote asset volume, number of trades,
    and taker buy volumes. It captures both standardized candlestick data and
    raw gateway-specific response data for additional information.

    Attributes:
        source: The source of the data (e.g., "binance").
        symbol: The symbol of the asset (e.g., "BTCUSDT").
        open_time: Opening time of the candle in unix timestamp seconds
            (e.g., 1704067200).
        open_price: Opening price of the candle (e.g., 42350.50).
        high_price: Highest price during the candle period (e.g., 42500.00).
        low_price: Lowest price during the candle period (e.g., 42300.00).
        close_price: Closing price of the candle (e.g., 42450.75).
        volume: Trading volume in base asset (e.g., 150.5 BTC).
        close_time: Closing time of the candle in unix timestamp seconds
            (e.g., 1704153600).
        quote_asset_volume: Trading volume in quote asset (e.g., 6380000.00 USDT).
        number_of_trades: Number of trades executed during the period (e.g., 1500).
        taker_buy_base_asset_volume: Taker buy volume in base asset
            (e.g., 75.2 BTC).
        taker_buy_quote_asset_volume: Taker buy volume in quote asset
            (e.g., 3190000.00 USDT).
        response: Raw broker-specific data for additional information.
    """

    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        str_strip_whitespace=True,
    )

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
    # PRIVATE METHODS
    # ───────────────────────────────────────────────────────────
    @field_validator(
        "open_time",
        "close_time",
        "number_of_trades",
        mode="before",
    )
    @classmethod
    def parse_int(cls, value: Any) -> int:
        """
        Parse and convert value to integer for time and trade count fields.

        Converts various input formats (string, int, float) to an integer.
        Returns 0 if conversion fails.

        Args:
            value: The value to parse. Can be None, empty string, float, int,
                or string representation of a number.

        Returns:
            int: The parsed integer value, or 0 if conversion fails.

        Example:
            >>> GatewayKlineModel.parse_int("1704067200")
            1704067200
            >>> GatewayKlineModel.parse_int(1500.5)
            1500
            >>> GatewayKlineModel.parse_int(None)
            0
        """
        return parse_int_helper(value=value)

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
        """
        Parse and convert value to float for price and volume fields.

        Converts various input formats (string, int, float) to a float.
        Returns 0.0 if conversion fails.

        Args:
            value: The value to parse. Can be None, empty string, float, int,
                or string representation of a number.

        Returns:
            float: The parsed float value, or 0.0 if conversion fails.

        Example:
            >>> GatewayKlineModel.parse_float("42350.50")
            42350.5
            >>> GatewayKlineModel.parse_float(150)
            150.0
            >>> GatewayKlineModel.parse_float(None)
            0.0
        """
        return parse_float_helper(value=value)
