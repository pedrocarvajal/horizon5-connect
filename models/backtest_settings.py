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
        return {
            "id": self.id,
            "enabled": self.enabled,
            "allocation": self.allocation,
            "leverage": self.leverage,
            "settings": self.settings,
        }


class AssetSettingsModel(BaseModel):
    """Configuration settings for a trading asset within a backtest."""

    symbol: str
    gateway: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert asset settings to dictionary representation."""
        return {
            "symbol": self.symbol,
            "gateway": self.gateway,
        }


class PortfolioSettingsModel(BaseModel):
    """Configuration settings for a portfolio within a backtest."""

    id: str
    path: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert portfolio settings to dictionary representation."""
        return {
            "id": self.id,
            "path": self.path,
        }


def _empty_strategies_list() -> List[StrategySettingsModel]:
    return []


class BacktestSettingsModel(BaseModel):
    """Complete configuration settings for a backtest execution."""

    from_date: int = Field(description="Start timestamp in seconds")
    to_date: int = Field(description="End timestamp in seconds")
    portfolio: PortfolioSettingsModel
    asset: AssetSettingsModel
    strategies: List[StrategySettingsModel] = Field(default_factory=_empty_strategies_list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert backtest settings to dictionary representation."""
        return {
            "from_date": self.from_date,
            "to_date": self.to_date,
            "portfolio": self.portfolio.to_dict(),
            "asset": self.asset.to_dict(),
            "strategies": [s.to_dict() for s in self.strategies],
        }
