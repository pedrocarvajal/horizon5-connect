from typing import List


def get_expected_shortfall(
    nav_history: List[float],
    confidence_level: float = 0.95,
) -> float:
    """
    Calculate Expected Shortfall (Conditional Value at Risk - CVaR).

    Args:
        nav_history: List of Net Asset Values over time
        confidence_level: Confidence level (default 0.95 = 95%)

    Returns:
        Average return in the worst (1 - confidence_level) tail
        Negative values indicate expected loss in worst scenarios
        Returns 0.0 if insufficient data

    Interpretation:
        Measures average loss in worst 5% of days (default)
        -0.01: Average -1% loss on worst days
        -0.05: Average -5% loss on worst days
        More negative = higher tail risk
        Closer to 0 = lower tail risk
    """
    returns = []
    min_observations = 2

    if len(nav_history) < min_observations:
        return 0.0

    for i in range(1, len(nav_history)):
        if nav_history[i - 1] == 0:
            continue

        previous_nav = nav_history[i - 1]
        current_nav = nav_history[i]
        daily_return = (current_nav - previous_nav) / previous_nav
        returns.append(daily_return)

    if len(returns) == 0:
        return 0.0

    sorted_returns = sorted(returns)
    tail_percentage = 1 - confidence_level
    tail_size = max(1, int(len(sorted_returns) * tail_percentage))
    tail_returns = sorted_returns[:tail_size]

    return sum(tail_returns) / len(tail_returns)
