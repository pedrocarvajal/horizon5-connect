"""Analytics services for performance metrics calculation.

This module implements the Composite pattern for analytics:
- StrategyAnalytic: Leaf component that calculates metrics from orderbook
- AssetAnalytic: Composite that aggregates strategy metrics
- PortfolioAnalytic: Composite that aggregates asset metrics
"""

from vendor.services.analytic.asset import AssetAnalytic
from vendor.services.analytic.portfolio import PortfolioAnalytic
from vendor.services.analytic.strategy import StrategyAnalytic

__all__ = [
    "AssetAnalytic",
    "PortfolioAnalytic",
    "StrategyAnalytic",
]
