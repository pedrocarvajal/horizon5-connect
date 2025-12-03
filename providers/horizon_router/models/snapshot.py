from typing import Optional
from pydantic import BaseModel, Field, ValidationInfo, field_validator
from enums.snapshot_event import SnapshotEvent

class SnapshotListQueryModel(BaseModel):
    strategy_id: Optional[str] = Field(default=None, description='Filter snapshots by strategy ID')
    asset_id: Optional[str] = Field(default=None, description='Filter snapshots by asset ID')
    backtest_id: Optional[str] = Field(default=None, description='Filter snapshots by backtest ID')
    backtest: Optional[bool] = Field(default=None, description='Filter snapshots by backtest flag')
    event: Optional[str] = Field(default=None, description='Filter snapshots by event (comma-separated)')
    per_page: Optional[int] = Field(default=15, ge=1, le=100, description='Number of results per page')
    page: Optional[int] = Field(default=1, ge=1, description='Page number')

class SnapshotCreateModel(BaseModel):
    strategy_id: str = Field(description='Strategy ID')
    asset_id: str = Field(description='Asset ID')
    backtest_id: Optional[str] = Field(default=None, description='Backtest ID')
    backtest: Optional[bool] = Field(default=False, description='Is backtest snapshot')
    event: SnapshotEvent = Field(description='Snapshot event')
    nav: float = Field(gt=0, description='Net Asset Value (must be positive)')
    allocation: float = Field(ge=0, le=1, description='Asset allocation (0-1)')
    nav_peak: Optional[float] = Field(default=None, gt=0, description='Peak NAV (must be positive)')
    r2: Optional[float] = Field(default=None, ge=0, le=1, description='R-squared (0-1)')
    cagr: Optional[float] = Field(default=None, description='Compound Annual Growth Rate')
    calmar_ratio: Optional[float] = Field(default=None, description='Calmar Ratio')
    expected_shortfall: Optional[float] = Field(default=None, description='Expected Shortfall')
    max_drawdown: Optional[float] = Field(default=None, ge=0, le=1, description='Maximum Drawdown (0-1)')
    profit_factor: Optional[float] = Field(default=None, ge=0, description='Profit Factor (non-negative)')
    recovery_factor: Optional[float] = Field(default=None, ge=0, description='Recovery Factor (non-negative)')
    sharpe_ratio: Optional[float] = Field(default=None, description='Sharpe Ratio')
    sortino_ratio: Optional[float] = Field(default=None, description='Sortino Ratio')
    ulcer_index: Optional[float] = Field(default=None, ge=0, description='Ulcer Index (non-negative)')

    @field_validator('nav_peak')
    @classmethod
    def validate_nav_peak(cls, v: Optional[float], info: ValidationInfo) -> Optional[float]:
        if v is not None and 'nav' in info.data and (info.data['nav'] is not None) and (v < info.data['nav']):
            raise ValueError('nav_peak must be greater than or equal to nav')
        return v

class SnapshotUpdateModel(BaseModel):
    event: Optional[SnapshotEvent] = Field(default=None, description='Snapshot event')
    nav: Optional[float] = Field(default=None, gt=0, description='Net Asset Value (must be positive)')
    allocation: Optional[float] = Field(default=None, ge=0, le=1, description='Asset allocation (0-1)')
    nav_peak: Optional[float] = Field(default=None, gt=0, description='Peak NAV (must be positive)')
    r2: Optional[float] = Field(default=None, ge=0, le=1, description='R-squared (0-1)')
    cagr: Optional[float] = Field(default=None, description='Compound Annual Growth Rate')
    calmar_ratio: Optional[float] = Field(default=None, description='Calmar Ratio')
    expected_shortfall: Optional[float] = Field(default=None, description='Expected Shortfall')
    max_drawdown: Optional[float] = Field(default=None, ge=0, le=1, description='Maximum Drawdown (0-1)')
    profit_factor: Optional[float] = Field(default=None, ge=0, description='Profit Factor (non-negative)')
    recovery_factor: Optional[float] = Field(default=None, ge=0, description='Recovery Factor (non-negative)')
    sharpe_ratio: Optional[float] = Field(default=None, description='Sharpe Ratio')
    sortino_ratio: Optional[float] = Field(default=None, description='Sortino Ratio')
    ulcer_index: Optional[float] = Field(default=None, ge=0, description='Ulcer Index (non-negative)')

    @field_validator('nav_peak')
    @classmethod
    def validate_nav_peak(cls, v: Optional[float], info: ValidationInfo) -> Optional[float]:
        if v is not None and 'nav' in info.data and (info.data['nav'] is not None) and (v < info.data['nav']):
            raise ValueError('nav_peak must be greater than or equal to nav')
        return v
