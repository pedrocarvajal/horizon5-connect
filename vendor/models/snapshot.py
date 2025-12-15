"""Performance snapshot model with analytics and metrics tracking."""

import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from vendor.enums.snapshot_event import SnapshotEvent
from vendor.services.logging import LoggingService


class SnapshotModel(BaseModel):
    """Performance snapshot with financial metrics and historical tracking.

    Attributes:
        backtest: Whether snapshot is from backtest.
        strategy_id: Associated strategy identifier.
        event: Snapshot trigger event.
        allocation: Capital allocation.
        nav: Net asset value.
        nav_peak: Historical NAV peak.
        r2: R-squared coefficient.
        cagr: Compound annual growth rate.
        sharpe_ratio: Risk-adjusted return metric.
        max_drawdown: Maximum drawdown from peak.
        performance_history: Historical performance values.
        nav_history: Historical NAV values.
        profit_history: Historical profit values.
    """

    backtest: bool = Field(default=False)
    backtest_id: Optional[str] = None
    portfolio_id: Optional[str] = None
    strategy_id: str = Field(...)
    asset_id: Optional[str] = None
    event: Optional[SnapshotEvent] = Field(default=None)
    allocation: float = Field(default=0, ge=0)
    nav: float = Field(default=0, ge=0)
    nav_peak: float = Field(default=0, ge=0)
    benchmark_initial_price: float = Field(default=0, ge=0)
    benchmark_current_price: float = Field(default=0, ge=0)

    r2: float = Field(default=0, ge=0, le=1)
    cagr: float = Field(default=0)
    calmar_ratio: float = Field(default=0)
    expected_shortfall: float = Field(default=0, le=0)
    max_drawdown: float = Field(default=0, le=0)
    profit_factor: float = Field(default=0, ge=0)
    recovery_factor: float = Field(default=0, ge=0)
    sharpe_ratio: float = Field(default=0)
    sortino_ratio: float = Field(default=0)
    ulcer_index: float = Field(default=0, ge=0)
    win_ratio: float = Field(default=0, ge=0, le=1)
    total_orders: int = Field(default=0, ge=0)
    total_buy_orders: int = Field(default=0, ge=0)
    total_sell_orders: int = Field(default=0, ge=0)
    average_trade_duration: float = Field(default=0, ge=0)
    daily_performance: float = Field(default=0)
    daily_performance_percentage: float = Field(default=0)
    days_elapsed: int = Field(default=0, ge=0)
    quality: float = Field(default=0, ge=0, le=1)
    quality_vs_benchmark: float = Field(
        default=0,
        ge=0,
        le=1,
        description=(
            "Quality score comparing strategy vs benchmark. Combines alpha, information ratio, and excess Sharpe."
        ),
    )

    alpha: float = Field(
        default=0,
        description="Excess return over benchmark after adjusting for beta. Positive alpha indicates outperformance.",
    )
    beta: float = Field(
        default=0,
        description="Sensitivity to benchmark movements. Beta > 1 means more volatile than benchmark.",
    )
    correlation: float = Field(
        default=0,
        ge=-1,
        le=1,
        description="Linear relationship between strategy and benchmark returns. Range: -1 (inverse) to 1 (perfect).",
    )
    tracking_error: float = Field(
        default=0,
        ge=0,
        description="Standard deviation of return differences vs benchmark. Lower means closer tracking.",
    )
    information_ratio: float = Field(
        default=0,
        description="Alpha divided by tracking error. Measures risk-adjusted excess return vs benchmark.",
    )

    performance_history: List[float] = Field(default_factory=lambda: [])
    nav_history: List[float] = Field(default_factory=lambda: [])
    profit_history: List[float] = Field(default_factory=lambda: [])
    benchmark_price_history: List[float] = Field(default_factory=lambda: [])

    created_at: Optional[datetime.datetime] = None

    def __init__(self, **kwargs: Any) -> None:
        """Initialize snapshot model and setup logging.

        Args:
            **kwargs: Snapshot attributes.
        """
        super().__init__(**kwargs)

        self._log = LoggingService()

    def to_dict(self) -> Dict[str, Any]:
        """Convert snapshot to dictionary representation for API.

        Returns:
            Dictionary with identifiers at root level and metrics in 'data' field.
        """
        result: Dict[str, Any] = {
            "strategy_id": self.strategy_id,
            "event": self.event.value if self.event else None,
            "backtest": self.backtest,
            "data": {
                "nav": self.nav,
                "allocation": self.allocation,
                "performance": self.performance,
                "performance_percentage": self.performance_percentage,
                "nav_peak": self.nav_peak,
                "r2": self.r2,
                "cagr": self.cagr,
                "calmar_ratio": self.calmar_ratio,
                "expected_shortfall": self.expected_shortfall,
                "max_drawdown": self.max_drawdown,
                "profit_factor": self.profit_factor,
                "recovery_factor": self.recovery_factor,
                "sharpe_ratio": self.sharpe_ratio,
                "sortino_ratio": self.sortino_ratio,
                "ulcer_index": self.ulcer_index,
                "win_ratio": self.win_ratio,
                "total_orders": self.total_orders,
                "total_buy_orders": self.total_buy_orders,
                "total_sell_orders": self.total_sell_orders,
                "average_trade_duration": self.average_trade_duration,
                "daily_performance": self.daily_performance,
                "daily_performance_percentage": self.daily_performance_percentage,
                "quality": self.quality,
                "quality_vs_benchmark": self.quality_vs_benchmark,
                "days_elapsed": self.days_elapsed,
                "benchmark_performance": self.benchmark_performance,
                "benchmark_performance_percentage": self.benchmark_performance_percentage,
                "alpha": self.alpha,
                "beta": self.beta,
                "correlation": self.correlation,
                "tracking_error": self.tracking_error,
                "information_ratio": self.information_ratio,
            },
        }

        if self.backtest_id:
            result["backtest_id"] = self.backtest_id

        if self.portfolio_id:
            result["portfolio_id"] = self.portfolio_id

        if self.asset_id:
            result["asset_id"] = self.asset_id

        return result

    @property
    def performance(self) -> float:
        """Calculate absolute performance as NAV minus allocation.

        Returns:
            Performance in currency units.
        """
        return self.nav - self.allocation

    @property
    def performance_percentage(self) -> float:
        """Calculate performance as percentage of allocation.

        Returns:
            Performance percentage (0.0 if allocation is 0).
        """
        if self.allocation == 0:
            return 0.0

        return self.performance / self.allocation

    @property
    def drawdown(self) -> float:
        """Calculate current drawdown from NAV peak.

        Returns:
            Drawdown as negative percentage (0.0 if no peak).
        """
        if self.nav_peak == 0:
            return 0.0

        return (self.nav - self.nav_peak) / self.nav_peak

    @property
    def benchmark_performance(self) -> float:
        """Calculate absolute benchmark performance from initial price.

        Returns:
            Benchmark performance in currency units.
        """
        return self.benchmark_current_price - self.benchmark_initial_price

    @property
    def benchmark_performance_percentage(self) -> float:
        """Calculate benchmark performance as percentage.

        Returns:
            Benchmark performance percentage (0.0 if initial price is 0).
        """
        if self.benchmark_initial_price == 0:
            return 0.0

        return self.benchmark_performance / self.benchmark_initial_price
