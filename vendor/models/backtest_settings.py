"""Backtest configuration models for strategy and execution settings."""

from typing import Any, Dict, List

from pydantic import BaseModel, Field


class StrategySettingsModel(BaseModel):
    """Configuration settings for a single trading strategy within a backtest."""

    id: str
    enabled: bool = Field(default=True)
    allocation: float = Field(default=0.0, ge=0)
    leverage: int = Field(default=1, ge=1)
    settings: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert strategy settings to dictionary representation."""
        return self.model_dump()


class AssetSettingsModel(BaseModel):
    """Configuration settings for a trading asset within a backtest."""

    symbol: str
    gateway: str
    strategies: List[StrategySettingsModel] = Field(default_factory=lambda: [])

    def to_dict(self) -> Dict[str, Any]:
        """Convert asset settings to dictionary representation."""
        return self.model_dump()


class PortfolioSettingsModel(BaseModel):
    """Configuration settings for a portfolio within a backtest."""

    id: str
    path: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert portfolio settings to dictionary representation."""
        return self.model_dump()


class BacktestSettingsModel(BaseModel):
    """Complete configuration settings for a backtest execution."""

    from_date: int = Field(description="Start timestamp in seconds")
    to_date: int = Field(description="End timestamp in seconds")
    portfolio: PortfolioSettingsModel
    assets: List[AssetSettingsModel] = Field(default_factory=lambda: [])

    def to_dict(self) -> Dict[str, Any]:
        """Convert backtest settings to dictionary representation."""
        return self.model_dump()
