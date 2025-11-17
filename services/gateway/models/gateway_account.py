# Last coding review: 2025-11-17 16:47:10
from typing import Any, List

from pydantic import BaseModel, ConfigDict, Field


class GatewayAccountBalanceModel(BaseModel):
    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    model_config = ConfigDict(arbitrary_types_allowed=True)

    asset: str = Field(
        default="",
        description="The asset symbol, like BTC or USDT",
    )
    balance: float = Field(
        default=0.0,
        description="Total balance of the asset",
    )
    locked: float = Field(
        default=0.0,
        description="Locked balance (unavailable for trading)",
    )
    response: Any = Field(
        default=None,
        description="Raw balance data for additional information",
    )


class GatewayAccountModel(BaseModel):
    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    model_config = ConfigDict(arbitrary_types_allowed=True)

    balances: List[GatewayAccountBalanceModel] = Field(
        default_factory=list,
        description="List of account balances by asset",
    )
    balance: float = Field(
        default=0.0,
        description="Total account balance (cash + positions value)",
    )
    nav: float = Field(
        default=0.0,
        description="Net Asset Value - total account equity",
    )
    locked: float = Field(
        default=0.0,
        description="Total locked funds (in orders, pending, etc.)",
    )
    margin: float = Field(
        default=0.0,
        description="Margin used for open positions",
    )
    exposure: float = Field(
        default=0.0,
        description="Total exposure (notional value of open positions)",
    )
    pnl: float = Field(
        default=0.0,
        description="Profit and Loss (realized + unrealized)",
    )
    response: Any = Field(
        default=None,
        description="Raw broker-specific account data for additional information",
    )
