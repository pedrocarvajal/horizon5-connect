import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from enums.snapshot_event import SnapshotEvent
from services.logging import LoggingService


class SnapshotModel(BaseModel):
    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    backtest: bool = Field(default=False)
    backtest_id: str = Field(...)
    strategy_id: str = Field(...)
    event: Optional[SnapshotEvent] = Field(default=None)
    nav: Optional[float] = Field(default=0, ge=0)
    allocation: Optional[float] = Field(default=0, ge=0)
    nav_peak: Optional[float] = Field(default=0, ge=0)

    r2: Optional[float] = Field(default=0, ge=0, le=1)
    cagr: Optional[float] = Field(default=0)
    calmar_ratio: Optional[float] = Field(default=0)
    expected_shortfall: Optional[float] = Field(default=0, le=0)
    max_drawdown: Optional[float] = Field(default=0, le=0)
    profit_factor: Optional[float] = Field(default=0, ge=0)
    recovery_factor: Optional[float] = Field(default=0, ge=0)
    sharpe_ratio: Optional[float] = Field(default=0)
    sortino_ratio: Optional[float] = Field(default=0)
    ulcer_index: Optional[float] = Field(default=0, ge=0)

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
            "event": self.event.value if self.event else None,
            "nav": self.nav,
            "allocation": self.allocation,
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
