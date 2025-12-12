"""Calculate Jensen's Alpha for benchmark comparison."""

from typing import List


def get_alpha(strategy_returns: List[float], benchmark_returns: List[float], beta: float) -> float:
    """Calculate Jensen's Alpha - excess return adjusted for systematic risk.

    Alpha measures the strategy's excess return compared to the benchmark
    after adjusting for market risk (beta).
    Formula: Alpha = Mean(strategy_returns) - Beta * Mean(benchmark_returns)

    Args:
        strategy_returns: List of strategy daily returns.
        benchmark_returns: List of benchmark daily returns.
        beta: Beta coefficient of the strategy.

    Returns:
        Alpha value representing excess return (0.0 if insufficient data).
    """
    min_observations = 2

    if len(strategy_returns) < min_observations or len(benchmark_returns) < min_observations:
        return 0.0

    if len(strategy_returns) != len(benchmark_returns):
        return 0.0

    strategy_mean_return = sum(strategy_returns) / len(strategy_returns)
    benchmark_mean_return = sum(benchmark_returns) / len(benchmark_returns)

    return strategy_mean_return - (beta * benchmark_mean_return)
