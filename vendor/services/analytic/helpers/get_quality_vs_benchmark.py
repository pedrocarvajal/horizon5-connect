"""Calculate quality score relative to benchmark performance."""

from typing import List

from vendor.enums.quality_vs_benchmark_method import QualityVsBenchmarkMethod

DAYS_PER_YEAR = 365
MIN_OBSERVATIONS = 2


def get_quality_vs_benchmark(
    method: QualityVsBenchmarkMethod,
    alpha: float,
    information_ratio: float,
    strategy_nav_history: List[float],
    benchmark_price_history: List[float],
    benchmark_initial_price: float,
) -> float:
    """Calculate quality score comparing strategy performance against benchmark.

    Args:
        method: Method to use for quality calculation.
        alpha: Excess return over benchmark after beta adjustment.
        information_ratio: Alpha divided by tracking error.
        strategy_nav_history: Historical NAV values for the strategy.
        benchmark_price_history: Historical prices of the benchmark.
        benchmark_initial_price: Initial benchmark price for return calculation.

    Returns:
        Quality score normalized to [0, 1] range.

    Interpretation:
        > 0.80: Excellent - significantly outperforms benchmark
        0.60-0.80: Good - consistently beats benchmark
        0.40-0.60: Average - roughly matches benchmark
        0.20-0.40: Below average - underperforms benchmark
        < 0.20: Poor - significantly worse than benchmark
    """
    if len(strategy_nav_history) < MIN_OBSERVATIONS or len(benchmark_price_history) < MIN_OBSERVATIONS:
        return 0.0

    if benchmark_initial_price == 0:
        return 0.0

    if method == QualityVsBenchmarkMethod.ALPHA:
        return round(_calculate_alpha_quality(alpha), 4)

    if method == QualityVsBenchmarkMethod.INFORMATION_RATIO:
        return round(_calculate_information_ratio_quality(information_ratio), 4)

    if method == QualityVsBenchmarkMethod.EXCESS_SHARPE:
        excess_sharpe_quality = _calculate_excess_sharpe_quality(
            strategy_nav_history,
            benchmark_price_history,
            benchmark_initial_price,
        )
        return round(excess_sharpe_quality, 4)

    alpha_quality = _calculate_alpha_quality(alpha)
    information_ratio_quality = _calculate_information_ratio_quality(information_ratio)
    excess_sharpe_quality = _calculate_excess_sharpe_quality(
        strategy_nav_history,
        benchmark_price_history,
        benchmark_initial_price,
    )

    weighted_score = alpha_quality * 0.35 + information_ratio_quality * 0.35 + excess_sharpe_quality * 0.30

    return round(weighted_score, 4)


def _calculate_alpha_quality(alpha: float) -> float:
    """Normalize alpha to quality score between 0 and 1.

    Thresholds:
        - alpha <= -0.20: quality = 0.0 (losing 20% or more vs benchmark)
        - alpha >= 0.20: quality = 1.0 (gaining 20% or more vs benchmark)
        - alpha = 0: quality = 0.5 (matching benchmark)

    Args:
        alpha: Annualized alpha value.

    Returns:
        Quality score between 0 and 1.
    """
    threshold_min = -0.20
    threshold_max = 0.20

    if alpha <= threshold_min:
        return 0.0
    if alpha >= threshold_max:
        return 1.0

    return (alpha - threshold_min) / (threshold_max - threshold_min)


def _calculate_information_ratio_quality(information_ratio: float) -> float:
    """Normalize information ratio to quality score between 0 and 1.

    Thresholds based on industry standards:
        - IR <= -0.50: quality = 0.0 (poor risk-adjusted alpha)
        - IR >= 1.00: quality = 1.0 (excellent risk-adjusted alpha)
        - IR = 0.50: quality = 0.67 (good)

    Args:
        information_ratio: Alpha divided by tracking error.

    Returns:
        Quality score between 0 and 1.
    """
    threshold_min = -0.50
    threshold_max = 1.00

    if information_ratio <= threshold_min:
        return 0.0
    if information_ratio >= threshold_max:
        return 1.0

    return (information_ratio - threshold_min) / (threshold_max - threshold_min)


def _calculate_excess_sharpe_quality(
    strategy_nav_history: List[float],
    benchmark_price_history: List[float],
    benchmark_initial_price: float,
) -> float:
    """Calculate quality based on difference between strategy and benchmark Sharpe ratios.

    Args:
        strategy_nav_history: Historical NAV values for the strategy.
        benchmark_price_history: Historical prices of the benchmark.
        benchmark_initial_price: Initial benchmark price.

    Returns:
        Quality score between 0 and 1.
    """
    strategy_sharpe = _calculate_sharpe_from_history(strategy_nav_history)
    benchmark_sharpe = _calculate_sharpe_from_prices(benchmark_price_history, benchmark_initial_price)

    excess_sharpe = strategy_sharpe - benchmark_sharpe

    threshold_min = -1.0
    threshold_max = 1.0

    if excess_sharpe <= threshold_min:
        return 0.0
    if excess_sharpe >= threshold_max:
        return 1.0

    return (excess_sharpe - threshold_min) / (threshold_max - threshold_min)


def _calculate_sharpe_from_history(nav_history: List[float]) -> float:
    """Calculate annualized Sharpe ratio from NAV history.

    Args:
        nav_history: List of NAV values over time.

    Returns:
        Annualized Sharpe ratio.
    """
    if len(nav_history) < MIN_OBSERVATIONS:
        return 0.0

    returns: List[float] = []
    for i in range(1, len(nav_history)):
        if nav_history[i - 1] == 0:
            continue
        daily_return = (nav_history[i] - nav_history[i - 1]) / nav_history[i - 1]
        returns.append(daily_return)

    if len(returns) < MIN_OBSERVATIONS:
        return 0.0

    mean_return = sum(returns) / len(returns)
    variance = sum((r - mean_return) ** 2 for r in returns) / (len(returns) - 1)
    standard_deviation = variance**0.5

    if standard_deviation == 0:
        return 0.0

    annualization_factor = DAYS_PER_YEAR**0.5
    return (mean_return / standard_deviation) * annualization_factor


def _calculate_sharpe_from_prices(
    price_history: List[float],
    initial_price: float,
) -> float:
    """Calculate annualized Sharpe ratio from price history.

    Args:
        price_history: List of prices over time.
        initial_price: Initial price for first return calculation.

    Returns:
        Annualized Sharpe ratio.
    """
    if len(price_history) < MIN_OBSERVATIONS or initial_price == 0:
        return 0.0

    returns: List[float] = []
    previous_price = initial_price

    for current_price in price_history:
        if previous_price == 0:
            previous_price = current_price
            continue
        daily_return = (current_price - previous_price) / previous_price
        returns.append(daily_return)
        previous_price = current_price

    if len(returns) < MIN_OBSERVATIONS:
        return 0.0

    mean_return = sum(returns) / len(returns)
    variance = sum((r - mean_return) ** 2 for r in returns) / (len(returns) - 1)
    standard_deviation = variance**0.5

    if standard_deviation == 0:
        return 0.0

    annualization_factor = DAYS_PER_YEAR**0.5
    return (mean_return / standard_deviation) * annualization_factor
