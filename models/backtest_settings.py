from typing import List

from pydantic import BaseModel, Field


class BacktestCommissionProfileBySymbolModel(BaseModel):
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


class BacktestSettingsModel(BaseModel):
    commission_by_symbols: List[BacktestCommissionProfileBySymbolModel] = Field(
        default_factory=list,
        description="Commission profiles keyed by symbol",
    )
