"""Performance snapshot model with analytics and metrics tracking."""

import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from vendor.enums.snapshot_event import SnapshotEvent
from vendor.services.logging import LoggingService


class SnapshotModel(BaseModel):
    """Performance snapshot with financial metrics and historical tracking.

    Organized in logical blocks:
        - Identifiers: IDs and metadata
        - Capital: NAV, allocation, monetary values
        - Performance: Returns, drawdown, CAGR
        - Risk: Sharpe, Sortino, Expected Shortfall
        - Trade: Orders, win ratio, profit factor
        - Benchmark: Comparisons vs benchmark
        - Score: Quality scores
        - History: Historical data arrays
        - Time: Dates and durations
    """

    # =========================================================================
    # IDENTIFIERS - IDs and metadata
    # =========================================================================
    strategy_id: str = Field(...)
    portfolio_id: Optional[str] = None
    asset_id: Optional[str] = None
    backtest_id: Optional[str] = None
    is_backtest: bool = Field(default=False)
    event: Optional[SnapshotEvent] = Field(default=None)

    # =========================================================================
    # CAPITAL - NAV, allocation, monetary values
    # =========================================================================
    capital_allocation: float = Field(default=0, ge=0)
    capital_nav: float = Field(default=0, ge=0)
    capital_nav_peak: float = Field(default=0, ge=0)
    capital_balance: float = Field(
        default=0,
        ge=0,
        description="Closed balance (realized P&L). Used for balance curve vs equity curve.",
    )
    capital_balance_peak: float = Field(
        default=0,
        ge=0,
        description="Historical peak of closed balance.",
    )

    # =========================================================================
    # PERFORMANCE - Returns, drawdown, CAGR
    # =========================================================================
    performance_r_squared: float = Field(default=0, ge=0, le=1)
    performance_cagr: float = Field(default=0)
    performance_max_drawdown: float = Field(default=0, le=0)
    performance_recovery_factor: float = Field(default=0, ge=0)
    performance_daily: float = Field(default=0)
    performance_daily_percentage: float = Field(default=0)

    # =========================================================================
    # RISK - Sharpe, Sortino, Expected Shortfall, Ulcer
    # =========================================================================
    risk_sharpe_ratio: float = Field(default=0)
    risk_sortino_ratio: float = Field(default=0)
    risk_calmar_ratio: float = Field(default=0)
    risk_expected_shortfall: float = Field(default=0, le=0)
    risk_ulcer_index: float = Field(default=0, ge=0)

    # =========================================================================
    # TRADE - Orders, win ratio, profit factor, duration
    # =========================================================================
    trade_profit_factor: float = Field(default=0, ge=0)
    trade_win_ratio: float = Field(default=0, ge=0, le=1)
    trade_total_orders: int = Field(default=0, ge=0)
    trade_buy_orders: int = Field(default=0, ge=0)
    trade_sell_orders: int = Field(default=0, ge=0)
    trade_average_duration: float = Field(default=0, ge=0)

    # =========================================================================
    # BENCHMARK - Comparisons vs benchmark
    # =========================================================================
    benchmark_initial_price: float = Field(default=0, ge=0)
    benchmark_current_price: float = Field(default=0, ge=0)
    benchmark_alpha: float = Field(
        default=0,
        description="Excess return over benchmark after adjusting for beta. Positive alpha indicates outperformance.",
    )
    benchmark_beta: float = Field(
        default=0,
        description="Sensitivity to benchmark movements. Beta > 1 means more volatile than benchmark.",
    )
    benchmark_correlation: float = Field(
        default=0,
        ge=-1,
        le=1,
        description="Linear relationship between strategy and benchmark returns. Range: -1 (inverse) to 1 (perfect).",
    )
    benchmark_tracking_error: float = Field(
        default=0,
        ge=0,
        description="Standard deviation of return differences vs benchmark. Lower means closer tracking.",
    )
    benchmark_information_ratio: float = Field(
        default=0,
        description="Alpha divided by tracking error. Measures risk-adjusted excess return vs benchmark.",
    )

    # =========================================================================
    # SCORE - Quality scores
    # =========================================================================
    score_quality: float = Field(default=0, ge=0, le=1)
    score_quality_vs_benchmark: float = Field(
        default=0,
        ge=0,
        le=1,
        description="Quality score comparing strategy vs benchmark.",
    )

    # =========================================================================
    # HISTORY - Historical data arrays
    # =========================================================================
    history_performance: List[float] = Field(default_factory=lambda: [])
    history_nav: List[float] = Field(default_factory=lambda: [])
    history_profit: List[float] = Field(default_factory=lambda: [])
    history_benchmark_price: List[float] = Field(default_factory=lambda: [])
    history_balance: List[float] = Field(
        default_factory=lambda: [],
        description="Historical closed balance values for balance curve.",
    )

    # =========================================================================
    # TIME - Dates and durations
    # =========================================================================
    time_days_elapsed: int = Field(default=0, ge=0)
    time_created_at: Optional[datetime.datetime] = None

    def __init__(self, **kwargs: Any) -> None:
        """Initialize snapshot model and setup logging.

        Args:
            **kwargs: Snapshot attributes.
        """
        super().__init__(**kwargs)

        self._log = LoggingService()

    def to_dict(self) -> Dict[str, Any]:
        """Convert snapshot metrics to dictionary representation.

        Returns only metrics, without identifiers (IDs should be added at report level).

        Returns:
            Dictionary with all snapshot metrics.
        """
        return {
            "capital_allocation": self.capital_allocation,
            "capital_nav": self.capital_nav,
            "capital_nav_peak": self.capital_nav_peak,
            "capital_balance": self.capital_balance,
            "capital_balance_peak": self.capital_balance_peak,
            "performance": self.performance,
            "performance_percentage": self.performance_percentage,
            "performance_r_squared": self.performance_r_squared,
            "performance_cagr": self.performance_cagr,
            "performance_max_drawdown": self.performance_max_drawdown,
            "performance_recovery_factor": self.performance_recovery_factor,
            "performance_daily": self.performance_daily,
            "performance_daily_percentage": self.performance_daily_percentage,
            "risk_sharpe_ratio": self.risk_sharpe_ratio,
            "risk_sortino_ratio": self.risk_sortino_ratio,
            "risk_calmar_ratio": self.risk_calmar_ratio,
            "risk_expected_shortfall": self.risk_expected_shortfall,
            "risk_ulcer_index": self.risk_ulcer_index,
            "trade_profit_factor": self.trade_profit_factor,
            "trade_win_ratio": self.trade_win_ratio,
            "trade_total_orders": self.trade_total_orders,
            "trade_buy_orders": self.trade_buy_orders,
            "trade_sell_orders": self.trade_sell_orders,
            "trade_average_duration": self.trade_average_duration,
            "benchmark_initial_price": self.benchmark_initial_price,
            "benchmark_current_price": self.benchmark_current_price,
            "benchmark_performance": self.benchmark_performance,
            "benchmark_performance_percentage": self.benchmark_performance_percentage,
            "benchmark_alpha": self.benchmark_alpha,
            "benchmark_beta": self.benchmark_beta,
            "benchmark_correlation": self.benchmark_correlation,
            "benchmark_tracking_error": self.benchmark_tracking_error,
            "benchmark_information_ratio": self.benchmark_information_ratio,
            "score_quality": self.score_quality,
            "score_quality_vs_benchmark": self.score_quality_vs_benchmark,
            "time_days_elapsed": self.time_days_elapsed,
        }

    @property
    def performance(self) -> float:
        """Calculate absolute performance as NAV minus allocation.

        Returns:
            Performance in currency units.
        """
        return self.capital_nav - self.capital_allocation

    @property
    def performance_percentage(self) -> float:
        """Calculate performance as percentage of allocation.

        Returns:
            Performance percentage (0.0 if allocation is 0).
        """
        if self.capital_allocation == 0:
            return 0.0

        return self.performance / self.capital_allocation

    @property
    def drawdown(self) -> float:
        """Calculate current drawdown from NAV peak.

        Returns:
            Drawdown as negative percentage (0.0 if no peak).
        """
        if self.capital_nav_peak == 0:
            return 0.0

        return (self.capital_nav - self.capital_nav_peak) / self.capital_nav_peak

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
