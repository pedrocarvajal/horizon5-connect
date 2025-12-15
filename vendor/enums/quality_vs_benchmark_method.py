"""Quality vs benchmark calculation method enumeration."""

from enum import Enum, unique


@unique
class QualityVsBenchmarkMethod(Enum):
    """Method for calculating quality score comparing strategy vs benchmark.

    Each method evaluates how well the strategy performs against a benchmark:
    - FQS_BENCHMARK: Weighted average of alpha (35%), information ratio (35%), excess sharpe (30%).
    - ALPHA: Based on alpha only (excess return over benchmark).
    - INFORMATION_RATIO: Based on information ratio only (alpha / tracking error).
    - EXCESS_SHARPE: Based on strategy sharpe minus benchmark sharpe.
    """

    FQS_BENCHMARK = "fqs_benchmark"
    ALPHA = "alpha"
    INFORMATION_RATIO = "information_ratio"
    EXCESS_SHARPE = "excess_sharpe"
