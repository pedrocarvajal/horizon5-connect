from pydantic import BaseModel, ConfigDict, Field, field_validator


class BinanceConfigModel(BaseModel):
    model_config = ConfigDict(frozen=True, validate_assignment=True)
    api_key: str = Field(min_length=1, description="Binance API key")
    api_secret: str = Field(min_length=1, description="Binance API secret")
    fapi_url: str = Field(min_length=1, description="Binance Futures API URL")
    fapi_v2_url: str = Field(min_length=1, description="Binance Futures API v2 URL")
    fapi_ws_url: str = Field(min_length=1, description="Binance Futures WebSocket URL")
    sandbox: bool = Field(default=False, description="Enable sandbox mode")

    @field_validator("api_key", "api_secret")
    @classmethod
    def validate_credentials(cls, v: str) -> str:
        if not v or v.strip() == "":
            raise ValueError("Credentials cannot be empty or whitespace")

        return v.strip()

    @field_validator("fapi_url", "fapi_v2_url")
    @classmethod
    def validate_http_urls(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")

        return v.strip()

    @field_validator("fapi_ws_url")
    @classmethod
    def validate_websocket_url(cls, v: str) -> str:
        if not v.startswith(("ws://", "wss://")):
            raise ValueError("WebSocket URL must start with ws:// or wss://")

        return v.strip()
