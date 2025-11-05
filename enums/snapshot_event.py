from enum import Enum


class SnapshotEvent(Enum):
    START_SNAPSHOT = "start_snapshot"
    ON_NEW_DAY = "on_new_day"
    BACKTEST_END = "backtest_end"
