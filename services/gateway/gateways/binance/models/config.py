# Code reviewed on 2025-11-19 by pedrocarvajal

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BinanceConfigModel(BaseModel):
    """
    Model representing Binance gateway configuration.

    This model stores Binance API credentials and endpoint URLs for both production
    and sandbox/testnet environments. It validates API keys, secrets, and URL formats
    to ensure proper configuration before gateway initialization.

    Attributes:
        api_key: Binance API key for authentication (optional, None for backtest mode).
        api_secret: Binance API secret for authentication (optional, None for backtest mode).
        fapi_url: Binance Futures API base URL (required, must start with http:// or https://).
        fapi_v2_url: Binance Futures API v2 base URL (required, must start with http:// or https://).
        fapi_ws_url: Binance Futures WebSocket URL (required, must start with ws:// or wss://).
        sandbox: Whether to use sandbox/testnet mode (default: False).
    """

    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    model_config = ConfigDict(
        frozen=True,
        validate_assignment=True,
    )
    api_key: Optional[str] = Field(
        default=None,
        description="Binance API key",
    )
    api_secret: Optional[str] = Field(
        default=None,
        description="Binance API secret",
    )
    fapi_url: str = Field(
        min_length=1,
        description="Binance Futures API URL",
    )
    fapi_v2_url: str = Field(
        min_length=1,
        description="Binance Futures API v2 URL",
    )
    fapi_ws_url: str = Field(
        min_length=1,
        description="Binance Futures WebSocket URL",
    )
    sandbox: bool = Field(
        default=False,
        description="Enable sandbox mode",
    )

    # ───────────────────────────────────────────────────────────
    # PRIVATE METHODS
    # ───────────────────────────────────────────────────────────
    @field_validator("api_key", "api_secret")
    @classmethod
    def validate_credentials(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate and normalize API credentials.

        Allows None for backtest mode. If a value is provided, ensures it's not
        empty or whitespace-only and strips leading and trailing whitespace.

        Args:
            v: The credential value to validate (API key or secret), or None.

        Returns:
            Optional[str]: The validated and stripped credential value, or None.

        Raises:
            ValueError: If the credential is empty string or contains only whitespace.

        Example:
            >>> BinanceConfigModel.validate_credentials("  my_api_key  ")
            "my_api_key"
            >>> BinanceConfigModel.validate_credentials(None)
            None
            >>> BinanceConfigModel.validate_credentials("")
            ValueError: Credentials cannot be empty or whitespace
        """
        if v is None:
            return None

        if v.strip() == "":
            raise ValueError("Credentials cannot be empty or whitespace")

        return v.strip()

    @field_validator("fapi_url", "fapi_v2_url")
    @classmethod
    def validate_http_urls(cls, v: str) -> str:
        """
        Validate and normalize HTTP/HTTPS URLs.

        Ensures that Futures API URLs start with http:// or https:// protocol.
        Strips leading and trailing whitespace from the URL.

        Args:
            v: The URL value to validate (fapi_url or fapi_v2_url).

        Returns:
            str: The validated and stripped URL value.

        Raises:
            ValueError: If the URL does not start with http:// or https://.

        Example:
            >>> BinanceConfigModel.validate_http_urls("https://fapi.binance.com")
            "https://fapi.binance.com"
            >>> BinanceConfigModel.validate_http_urls("ftp://example.com")
            ValueError: URL must start with http:// or https://
        """
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")

        return v.strip()

    @field_validator("fapi_ws_url")
    @classmethod
    def validate_websocket_url(cls, v: str) -> str:
        """
        Validate and normalize WebSocket URLs.

        Ensures that WebSocket URL starts with ws:// or wss:// protocol.
        Strips leading and trailing whitespace from the URL.

        Args:
            v: The WebSocket URL value to validate.

        Returns:
            str: The validated and stripped WebSocket URL value.

        Raises:
            ValueError: If the URL does not start with ws:// or wss://.

        Example:
            >>> BinanceConfigModel.validate_websocket_url("wss://fstream.binance.com")
            "wss://fstream.binance.com"
            >>> BinanceConfigModel.validate_websocket_url("http://example.com")
            ValueError: WebSocket URL must start with ws:// or wss://
        """
        if not v.startswith(("ws://", "wss://")):
            raise ValueError("WebSocket URL must start with ws:// or wss://")

        return v.strip()
