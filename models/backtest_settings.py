from typing import List, Optional

from pydantic import BaseModel, Field


class CommissionTierModel(BaseModel):
    threshold_notional: float = Field(
        ...,
        ge=0,
        description="Minimum notional in quote currency required for this tier",
    )
    commission_rate: float = Field(
        ...,
        ge=0,
        le=1,
        description="Commission rate for this tier, like 0.0005 for 0.05%",
    )


class CommissionProfileModel(BaseModel):
    symbol: str = Field(
        ...,
        description="Asset symbol, for example BTCUSDT",
    )
    buy_rate: float = Field(
        default=0.0,
        ge=0,
        le=1,
        description="Base commission rate on buy orders as decimal",
    )
    sell_rate: float = Field(
        default=0.0,
        ge=0,
        le=1,
        description="Base commission rate on sell orders as decimal",
    )
    flat_fee_per_trade: float = Field(
        default=0.0,
        ge=0,
        description="Fixed commission charged per executed order in quote currency",
    )
    spread_bps: float = Field(
        default=0.0,
        ge=0,
        description="Synthetic spread widening in basis points added to executions",
    )
    tiers: List[CommissionTierModel] = Field(
        default_factory=list,
        description="Optional volume tiers, evaluated from highest threshold to lowest",
    )
    maker_rate: Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
        description="Optional maker fee rate when providing liquidity",
    )
    taker_rate: Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
        description="Optional taker fee rate when removing liquidity",
    )


class BacktestSettingsModel(BaseModel):
    default_buy_rate: float = Field(
        default=0.0,
        ge=0,
        le=1,
        description="Fallback buy commission when no profile matches",
    )
    default_sell_rate: float = Field(
        default=0.0,
        ge=0,
        le=1,
        description="Fallback sell commission when no profile matches",
    )
    default_flat_fee_per_trade: float = Field(
        default=0.0,
        ge=0,
        description="Fallback fixed commission per order when no profile matches",
    )
    profiles: List[CommissionProfileModel] = Field(
        default_factory=list,
        description="Commission profiles keyed by symbol",
    )
