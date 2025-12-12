"""Order opening mode enumeration."""

from enum import Enum, unique


@unique
class OrderOpeningMode(str, Enum):
    """Order opening mode for strategy execution.

    Attributes:
        ONE_AT_A_TIME: Allow only one open order at a time.
        ONE_PER_DAY: Allow one order per calendar day.
        ONE_PER_WEEK: Allow one order per calendar week.
    """

    ONE_AT_A_TIME = "one_at_a_time"
    ONE_PER_DAY = "one_per_day"
    ONE_PER_WEEK = "one_per_week"

    def is_one_at_a_time(self) -> bool:
        """Check if mode is ONE_AT_A_TIME."""
        return self == OrderOpeningMode.ONE_AT_A_TIME

    def is_one_per_day(self) -> bool:
        """Check if mode is ONE_PER_DAY."""
        return self == OrderOpeningMode.ONE_PER_DAY

    def is_one_per_week(self) -> bool:
        """Check if mode is ONE_PER_WEEK."""
        return self == OrderOpeningMode.ONE_PER_WEEK
