"""Backtest expectation model for quality calculation thresholds."""

from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

EXPECTATION_RANGE_LENGTH = 2


class BacktestExpectationModel(BaseModel):
    """Expectation thresholds for backtest quality calculation.

    Each metric is defined as [minimum, expected] where:
    - Value < minimum → quality contribution = 0
    - Value >= expected → quality contribution = 1
    - Value between min and expected → linearly interpolated (0-1)

    For metrics where lower is better (like drawdown), the scale is inverted:
    - Value <= expected → quality contribution = 1
    - Value >= minimum → quality contribution = 0

    Attributes:
        num_trades: [min, expected] number of trades for statistical significance.
        max_drawdown: [min, expected] maximum drawdown (negative values, e.g., [-0.30, -0.05]).
        performance_percentage: [min, expected] total return percentage.
        profit_factor: [min, expected] gross profit / gross loss ratio.
        win_ratio: [min, expected] ratio of winning trades (0-1).
        r_squared: [min, expected] equity curve linearity (0-1).
        recovery_factor: [min, expected] net profit / max drawdown ratio.
        trade_duration: [min, expected] average trade duration in minutes.
    """

    num_trades: Optional[List[float]] = Field(
        default=None,
        description="[min, expected] number of trades",
    )
    max_drawdown: Optional[List[float]] = Field(
        default=None,
        description="[min, expected] maximum drawdown (negative values)",
    )
    performance_percentage: Optional[List[float]] = Field(
        default=None,
        description="[min, expected] total return percentage",
    )
    profit_factor: Optional[List[float]] = Field(
        default=None,
        description="[min, expected] profit factor",
    )
    win_ratio: Optional[List[float]] = Field(
        default=None,
        description="[min, expected] ratio of winning trades (0-1)",
    )
    r_squared: Optional[List[float]] = Field(
        default=None,
        description="[min, expected] R² of equity curve",
    )
    recovery_factor: Optional[List[float]] = Field(
        default=None,
        description="[min, expected] recovery factor",
    )
    trade_duration: Optional[List[float]] = Field(
        default=None,
        description="[min, expected] average trade duration in minutes",
    )

    def get_range(self, metric: str) -> Optional[Tuple[float, float]]:
        """Get the [min, expected] range for a metric.

        Args:
            metric: Name of the metric to retrieve.

        Returns:
            Tuple of (minimum, expected) or None if not defined.
        """
        value = getattr(self, metric, None)
        if value is not None and len(value) == EXPECTATION_RANGE_LENGTH:
            return (value[0], value[1])
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        return {k: v for k, v in self.model_dump().items() if v is not None}

    @classmethod
    def default(cls) -> "BacktestExpectationModel":
        """Return default expectation thresholds for backtest quality calculation."""
        return cls(
            num_trades=[10, 50],
            max_drawdown=[-0.30, -0.05],
            performance_percentage=[0.05, 0.30],
            profit_factor=[1.0, 2.0],
            win_ratio=[0.40, 0.60],
            r_squared=[0.3, 0.8],
            recovery_factor=[1.0, 3.0],
            trade_duration=[30, 240],
        )
