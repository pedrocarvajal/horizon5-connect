from typing import List


def get_sortino_ratio(
    nav_history: List[float],
    risk_free_rate: float = 0.0,
) -> float:
    """
    Calculate Sortino Ratio (annualized downside risk-adjusted return).

    Args:
        nav_history: List of Net Asset Values over time
        risk_free_rate: Risk-free rate as daily decimal (default 0.0)

    Returns:
        Annualized Sortino Ratio
        Returns 0.0 if insufficient data or no downside returns

    Interpretation:
        Measures excess return per unit of downside volatility
        Similar to Sharpe but only penalizes downside volatility
        > 2.0: Excellent - high returns with minimal downside
        1.0-2.0: Good downside risk management
        0.0-1.0: Poor downside protection
        < 0.0: Negative returns
        Often higher than Sharpe for asymmetric return distributions
    """
    min_observations = 2
    min_returns_for_variance = 2
    days_per_year = 365
    returns = []

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
    downside_returns = [r for r in returns if r < 0]

    if len(downside_returns) == 0:
        return 0.0

    downside_variance = sum(r**2 for r in downside_returns) / len(downside_returns)
    downside_deviation = downside_variance**0.5

    if downside_deviation == 0:
        return 0.0

    excess_return = mean_return - risk_free_rate
    annualization_factor = days_per_year**0.5

    return (excess_return / downside_deviation) * annualization_factor
