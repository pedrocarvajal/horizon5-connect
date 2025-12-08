"""Backtest event types for portfolio aggregation."""

from enum import Enum, unique


@unique
class BacktestEvent(str, Enum):
    """
    Represents events emitted during backtest execution.

    This enum is used for communication between BacktestService processes
    and PortfolioAggregator via the events queue.

    Members:
        BACKTEST_FINISHED: Signals that an asset backtest has finished with its report.
        BACKTEST_FAILED: Signals that an asset backtest has failed with an error.
    """

    BACKTEST_FINISHED = "backtest_finished"
    BACKTEST_FAILED = "backtest_failed"
