"""MetaAPI configuration model for API credentials and settings."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MetaApiConfigModel(BaseModel):
    """
    Model representing MetaAPI gateway configuration.

    Stores MetaAPI credentials and endpoint URLs for connecting to MetaTrader
    accounts via the MetaAPI cloud service.

    Attributes:
        auth_token: JWT authentication token for MetaAPI.
        account_id: MetaTrader account ID registered with MetaAPI.
        base_url: Base URL for the MetaAPI market data endpoint.
    """

    model_config = ConfigDict(
        frozen=True,
        validate_assignment=True,
    )

    auth_token: Optional[str] = Field(
        default=None,
        description="MetaAPI JWT authentication token",
    )
    account_id: Optional[str] = Field(
        default=None,
        description="MetaTrader account ID",
    )
    base_url: str = Field(
        default="https://mt-market-data-client-api-v1.new-york.agiliumtrade.ai",
        description="MetaAPI market data base URL",
    )

    @field_validator("auth_token", "account_id")
    @classmethod
    def validate_credentials(cls, value: Optional[str]) -> Optional[str]:
        """
        Validate and normalize API credentials.

        Args:
            value: The credential value to validate.

        Returns:
            The validated and stripped credential value, or None.

        Raises:
            ValueError: If the credential is empty or whitespace only.
        """
        if value is None:
            return None

        if value.strip() == "":
            raise ValueError("Credentials cannot be empty or whitespace")

        return value.strip()

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, value: str) -> str:
        """
        Validate and normalize base URL.

        Args:
            value: The URL value to validate.

        Returns:
            The validated and stripped URL value.

        Raises:
            ValueError: If the URL does not start with http:// or https://.
        """
        if not value.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")

        return value.strip().rstrip("/")
