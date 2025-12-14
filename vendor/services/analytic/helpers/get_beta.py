"""Calculate Beta coefficient for benchmark comparison."""

from typing import List


def get_beta(strategy_returns: List[float], benchmark_returns: List[float]) -> float:
    """Calculate Beta using covariance and variance.

    Beta measures the volatility of strategy returns relative to benchmark returns.
    Formula: Beta = Cov(strategy, benchmark) / Var(benchmark)

    Args:
        strategy_returns: List of strategy daily returns.
        benchmark_returns: List of benchmark daily returns.

    Returns:
        Beta coefficient (0.0 if insufficient data or zero variance).
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

    variance = sum((benchmark_returns[i] - benchmark_mean) ** 2 for i in range(n)) / n

    if variance == 0:
        return 0.0

    return covariance / variance
