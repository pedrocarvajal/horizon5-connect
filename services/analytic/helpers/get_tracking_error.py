"""Calculate tracking error for benchmark comparison."""

from typing import List


def get_tracking_error(strategy_returns: List[float], benchmark_returns: List[float]) -> float:
    """Calculate tracking error - standard deviation of excess returns.

    Tracking error measures the volatility of the difference between
    strategy returns and benchmark returns.
    Formula: TrackingError = StdDev(strategy_returns - benchmark_returns)

    Args:
        strategy_returns: List of strategy daily returns.
        benchmark_returns: List of benchmark daily returns.

    Returns:
        Tracking error as standard deviation (0.0 if insufficient data).
    """
    min_observations = 2

    if len(strategy_returns) < min_observations or len(benchmark_returns) < min_observations:
        return 0.0

    if len(strategy_returns) != len(benchmark_returns):
        return 0.0

    n = len(strategy_returns)

    excess_returns = [strategy_returns[i] - benchmark_returns[i] for i in range(n)]

    mean_excess = sum(excess_returns) / n

    variance = sum((excess_returns[i] - mean_excess) ** 2 for i in range(n)) / n

    return variance**0.5
