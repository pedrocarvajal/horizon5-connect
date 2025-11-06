from typing import List


def get_ulcer_index(nav_history: List[float]) -> float:
    """
    Calculate Ulcer Index (measure of downside volatility/stress).

    Args:
        nav_history: List of Net Asset Values over time

    Returns:
        Ulcer Index as percentage (RMS of drawdowns)
        Returns 0.0 if insufficient data or no drawdowns

    Interpretation:
        Measures depth and duration of drawdowns (investor stress)
        0-1%: Very low stress, minimal drawdowns
        1-5%: Low to moderate stress
        5-10%: Moderate stress
        > 10%: High stress, significant drawdowns
        Lower is better - indicates smoother equity curve
        Complements max drawdown by considering all drawdowns
    """
    min_observations = 2
    if len(nav_history) < min_observations:
        return 0.0

    squared_drawdowns = []
    peak = nav_history[0]

    for nav in nav_history:
        peak = max(peak, nav)

        if peak == 0:
            continue

        drawdown_percentage = ((nav - peak) / peak) * 100
        squared_drawdowns.append(drawdown_percentage**2)

    if len(squared_drawdowns) == 0:
        return 0.0

    mean_squared_drawdown = sum(squared_drawdowns) / len(squared_drawdowns)

    return mean_squared_drawdown**0.5
