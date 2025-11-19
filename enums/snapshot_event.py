# Code reviewed on 2025-01-27 by pedrocarvajal

from enum import Enum, unique


@unique
class SnapshotEvent(Enum):
    """
    Represents events that trigger analytics snapshot creation.

    Events occur during backtest execution to capture analytics at specific
    points: when snapshot tracking starts, on each new day, and when the
    backtest ends.
    """

    START_SNAPSHOT = "start_snapshot"
    ON_NEW_DAY = "on_new_day"
    BACKTEST_END = "backtest_end"
