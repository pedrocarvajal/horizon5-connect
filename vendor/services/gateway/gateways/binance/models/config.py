"""Binance configuration model for kline data retrieval."""

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BinanceConfigModel(BaseModel):
    """
    Model representing Binance gateway configuration for backtest data retrieval.

    Attributes:
        fapi_url: Binance Futures API base URL (must start with http:// or https://).
    """

    model_config = ConfigDict(
        frozen=True,
        validate_assignment=True,
    )
    fapi_url: str = Field(
        min_length=1,
        description="Binance Futures API URL",
    )

    @field_validator("fapi_url")
    @classmethod
    def validate_http_urls(cls, v: str) -> str:
        """Ensure the API URL starts with http:// or https://."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")

        return v.strip()
