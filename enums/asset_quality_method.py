"""Asset quality aggregation method enumeration."""

from enum import Enum, unique


@unique
class AssetQualityMethod(Enum):
    """Method for aggregating strategy qualities into asset quality.

    Attributes:
        WEIGHTED_AVERAGE: Weighted average by allocation (default).
            Formula: sum(quality_i * allocation_i) / sum(allocation_i)
            Use when: You want balanced representation of all strategies.
    """

    WEIGHTED_AVERAGE = "weighted_average"
