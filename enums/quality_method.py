"""Quality calculation method enumeration."""

from enum import Enum, unique


@unique
class QualityMethod(Enum):
    """Method for calculating strategy quality score.

    Each method evaluates backtest results against [min, expected] ranges:
    - Value < min → quality = 0
    - Value >= expected → quality = 1
    - Value between min and expected → linearly interpolated (0-1)

    Attributes:
        FQS: Final Quality Score - weighted average of all metrics (default).
        SORTINO: Based on Sortino ratio only (risk-adjusted, downside volatility).
        DRAWDOWN: Based on max drawdown only (inverted - lower is better).
        PERFORMANCE: Based on performance percentage only.
        PROFIT_FACTOR: Based on profit factor only.
        SHARPE: Based on Sharpe ratio only (risk-adjusted, total volatility).
        R_SQUARED: Based on R² only (equity curve consistency).
    """

    FQS = "fqs"
    SORTINO = "sortino"
    DRAWDOWN = "drawdown"
    PERFORMANCE = "performance"
    PROFIT_FACTOR = "profit_factor"
    SHARPE = "sharpe"
    R_SQUARED = "r_squared"
