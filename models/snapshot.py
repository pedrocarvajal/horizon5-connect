import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from enums.snapshot_event import SnapshotEvent
from services.logging import LoggingService


class SnapshotModel(BaseModel):
    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    backtest: bool = Field(default=False)
    backtest_id: Optional[str] = None
    strategy_id: str = Field(...)
    event: Optional[SnapshotEvent] = Field(default=None)
    allocation: float = Field(default=0, ge=0)
    nav: float = Field(default=0, ge=0)
    nav_peak: float = Field(default=0, ge=0)

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

    performance_history: List[float] = Field(default_factory=list)
    nav_history: List[float] = Field(default_factory=list)
    profit_history: List[float] = Field(default_factory=list)

    created_at: Optional[datetime.datetime] = None

    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        self._log = LoggingService()
        self._log.setup("snapshot_model")

    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def to_dict(self) -> Dict[str, Any]:
        return {
            "backtest": self.backtest,
            "backtest_id": self.backtest_id,
            "strategy_id": self.strategy_id,
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
            "created_at": self.created_at,
        }

    @property
    def performance(self) -> float:
        return self.nav - self.allocation

    @property
    def performance_percentage(self) -> float:
        if self.allocation == 0:
            return 0.0

        return self.performance / self.allocation

    @property
    def drawdown(self) -> float:
        if self.nav_peak == 0:
            return 0.0

        return (self.nav - self.nav_peak) / self.nav_peak
