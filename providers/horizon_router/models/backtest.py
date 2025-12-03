from typing import Optional
from pydantic import BaseModel, Field
from enums.backtest_status import BacktestStatus

class BacktestSettingsModel(BaseModel):
    asset: str = Field(description='Trading asset symbol (e.g., BTCUSDT)')
    strategies: str = Field(description='Comma-separated list of strategy IDs')
    from_date: int = Field(description='Start date as Unix timestamp')
    to_date: int = Field(description='End date as Unix timestamp')

class BacktestListQueryModel(BaseModel):
    user_id: Optional[str] = Field(default=None, description='Filter backtests by user ID')
    status: Optional[BacktestStatus] = Field(default=None, description='Filter backtests by status')
    per_page: Optional[int] = Field(default=15, ge=1, le=100, description='Number of results per page')
    page: Optional[int] = Field(default=1, ge=1, description='Page number')

class BacktestCreateModel(BaseModel):
    user_id: str = Field(description='User ID')
    status: Optional[BacktestStatus] = Field(default=BacktestStatus.PENDING, description='Backtest status')
    settings: Optional[BacktestSettingsModel] = Field(default=None, description='Backtest settings including asset, dates, strategy, etc.')

class BacktestUpdateModel(BaseModel):
    status: Optional[BacktestStatus] = Field(default=None, description='Backtest status')
    settings: Optional[BacktestSettingsModel] = Field(default=None, description='Backtest settings including asset, dates, strategy, etc.')
