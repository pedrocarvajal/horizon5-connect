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
        FQS: Final Quality Score - weighted average of performance, drawdown, r2.
        DRAWDOWN: Based on max drawdown only (inverted - lower is better).
        PROFIT_FACTOR: Based on profit factor only.
        R_SQUARED: Based on R² only (equity curve consistency).
        WIN_RATIO: Based on win ratio only (winning trades / total trades).
    """

    FQS = "fqs"
    DRAWDOWN = "drawdown"
    PROFIT_FACTOR = "profit_factor"
    R_SQUARED = "r_squared"
    WIN_RATIO = "win_ratio"
