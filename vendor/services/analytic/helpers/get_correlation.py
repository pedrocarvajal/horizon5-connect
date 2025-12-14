"""Calculate correlation coefficient for benchmark comparison."""

from typing import List


def get_correlation(strategy_returns: List[float], benchmark_returns: List[float]) -> float:
    """Calculate Pearson correlation coefficient between strategy and benchmark returns.

    Correlation measures the linear relationship between strategy and benchmark.
    Range: -1 (perfect negative correlation) to +1 (perfect positive correlation).
    Formula: Corr = Cov(strategy, benchmark) / (StdDev(strategy) * StdDev(benchmark))

    Args:
        strategy_returns: List of strategy daily returns.
        benchmark_returns: List of benchmark daily returns.

    Returns:
        Correlation coefficient between -1 and 1 (0.0 if insufficient data).
    """
    min_observations = 2

    if len(strategy_returns) < min_observations or len(benchmark_returns) < min_observations:
        return 0.0

    if len(strategy_returns) != len(benchmark_returns):
        return 0.0

    n = len(strategy_returns)

    strategy_mean = sum(strategy_returns) / n
    benchmark_mean = sum(benchmark_returns) / n

    covariance = (
        sum((strategy_returns[i] - strategy_mean) * (benchmark_returns[i] - benchmark_mean) for i in range(n)) / n
    )

    strategy_variance = sum((strategy_returns[i] - strategy_mean) ** 2 for i in range(n)) / n
    benchmark_variance = sum((benchmark_returns[i] - benchmark_mean) ** 2 for i in range(n)) / n

    strategy_std = strategy_variance**0.5
    benchmark_std = benchmark_variance**0.5

    if strategy_std == 0 or benchmark_std == 0:
        return 0.0

    correlation = covariance / (strategy_std * benchmark_std)

    return max(-1.0, min(1.0, correlation))
