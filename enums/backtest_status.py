# Code reviewed on 2025-11-19 by pedrocarvajal

from enum import Enum, unique


@unique
class BacktestStatus(Enum):
    """
    Represents the execution status of a backtest in the trading system.

    Backtests progress through states: PENDING -> RUNNING -> COMPLETED or FAILED.
    """

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
