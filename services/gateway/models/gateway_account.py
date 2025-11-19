# Code reviewed on 2025-01-27 by pedrocarvajal

from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class GatewayAccountBalanceModel(BaseModel):
    """
    Model representing an account balance for a single asset from a gateway/exchange.

    This model stores balance information for a specific asset including total balance,
    locked balance, and raw response data. It captures both standardized balance data
    and raw gateway-specific response data for additional information.

    Attributes:
        asset: The asset symbol (e.g., "BTC", "USDT").
        balance: Total balance of the asset. Must be >= 0.
        locked: Locked balance (unavailable for trading). Must be >= 0.
        response: Raw balance data for additional information.
    """

    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        str_strip_whitespace=True,
    )

    asset: str = Field(
        default="",
        description="The asset symbol, like BTC or USDT",
    )
    balance: float = Field(
        default=0.0,
        ge=0,
        description="Total balance of the asset",
    )
    locked: float = Field(
        default=0.0,
        ge=0,
        description="Locked balance (unavailable for trading)",
    )
    response: Optional[Any] = Field(
        default=None,
        description="Raw balance data for additional information",
    )


class GatewayAccountModel(BaseModel):
    """
    Model representing an account from a gateway/exchange.

    This model stores comprehensive account information including balances by asset,
    total balance, net asset value (NAV), margin, exposure, and profit/loss. It
    captures both standardized account data and raw gateway-specific response data
    for additional information.

    Attributes:
        balances: List of account balances by asset.
        balance: Total account balance (cash + positions value). Must be >= 0.
        nav: Net Asset Value - total account equity. Must be >= 0.
        locked: Total locked funds (in orders, pending, etc.). Must be >= 0.
        margin: Margin used for open positions. Must be >= 0.
        exposure: Total exposure (notional value of open positions). Must be >= 0.
        pnl: Profit and Loss (realized + unrealized).
        response: Raw broker-specific account data for additional information.
    """

    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        str_strip_whitespace=True,
    )
    balances: List[GatewayAccountBalanceModel] = Field(
        default_factory=list,
        description="List of account balances by asset",
    )
    balance: float = Field(
        default=0.0,
        ge=0,
        description="Total account balance (cash + positions value)",
    )
    nav: float = Field(
        default=0.0,
        ge=0,
        description="Net Asset Value - total account equity",
    )
    locked: float = Field(
        default=0.0,
        ge=0,
        description="Total locked funds (in orders, pending, etc.)",
    )
    margin: float = Field(
        default=0.0,
        ge=0,
        description="Margin used for open positions",
    )
    exposure: float = Field(
        default=0.0,
        ge=0,
        description="Total exposure (notional value of open positions)",
    )
    pnl: float = Field(
        default=0.0,
        description="Profit and Loss (realized + unrealized)",
    )
    response: Optional[Any] = Field(
        default=None,
        description="Raw broker-specific account data for additional information",
    )
