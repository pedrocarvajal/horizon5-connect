from typing import List


def get_sharpe_ratio(
    nav_history: List[float],
    risk_free_rate: float = 0.0,
) -> float:
    """
    Calculate Sharpe Ratio (annualized risk-adjusted return).

    Args:
        nav_history: List of Net Asset Values over time
        risk_free_rate: Risk-free rate as daily decimal (default 0.0)

    Returns:
        Annualized Sharpe Ratio
        Returns 0.0 if insufficient data or zero volatility

    Interpretation:
        Measures excess return per unit of total volatility
        > 3.0: Excellent risk-adjusted returns
        2.0-3.0: Very good
        1.0-2.0: Good
        0.0-1.0: Subpar
        < 0.0: Losing money with volatility
        Industry standard: > 1.0 is acceptable
    """
    returns = []
    min_observations = 2
    min_returns_for_variance = 2

    if len(nav_history) < min_observations:
        return 0.0

    for i in range(1, len(nav_history)):
        if nav_history[i - 1] == 0:
            continue

        previous_nav = nav_history[i - 1]
        current_nav = nav_history[i]
        daily_return = (current_nav - previous_nav) / previous_nav
        returns.append(daily_return)

    if len(returns) <= min_returns_for_variance:
        return 0.0

    mean_return = sum(returns) / len(returns)
    variance = sum((r - mean_return) ** 2 for r in returns) / (len(returns) - 1)
    std_dev = variance**0.5

    if std_dev == 0:
        return 0.0

    excess_return = mean_return - risk_free_rate
    days_per_year = 365
    annualization_factor = days_per_year**0.5

    return (excess_return / std_dev) * annualization_factor
