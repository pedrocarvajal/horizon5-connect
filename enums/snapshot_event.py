from enum import Enum


class SnapshotEvent(Enum):
    ON_NEW_DAY = "on_new_day"
    BACKTEST_END = "backtest_end"
