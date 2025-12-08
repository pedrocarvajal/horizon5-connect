"""Asset quality aggregation method enumeration."""

from enum import Enum, unique


@unique
class AssetQualityMethod(Enum):
    """Method for aggregating strategy qualities into asset quality.

    Each method provides a different perspective on asset quality:

    Attributes:
        WEIGHTED_AVERAGE: Weighted average by allocation (default).
            Formula: sum(quality_i * allocation_i) / sum(allocation_i)
            Use when: You want balanced representation of all strategies.

        MINIMUM: Conservative approach using minimum quality.
            Formula: min(quality_1, quality_2, ..., quality_n)
            Use when: Asset quality should reflect its weakest strategy.

        CONTRIBUTION_WEIGHTED: Weighted by actual P&L contribution.
            Formula: sum(quality_i * abs(performance_i)) / sum(abs(performance_i))
            Use when: Strategies with higher impact should weight more.

        CORRELATION_ADJUSTED: Adjusted for strategy correlation.
            Penalizes highly correlated strategies (less diversification benefit).
            Use when: You want to account for diversification effects.
    """

    WEIGHTED_AVERAGE = "weighted_average"
    MINIMUM = "minimum"
    CONTRIBUTION_WEIGHTED = "contribution_weighted"
    CORRELATION_ADJUSTED = "correlation_adjusted"
