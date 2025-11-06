def get_recovery_factor(
    net_profit_percentage: float,
    max_drawdown: float,
) -> float:
    """
    Calculate Recovery Factor (net profit to maximum drawdown ratio).

    Args:
        net_profit_percentage: Total return as decimal (e.g., 0.035 = 3.5%)
        max_drawdown: Maximum drawdown as negative decimal (e.g., -0.05 = -5%)

    Returns:
        Recovery Factor as ratio (net_profit% / |max_drawdown%|)
        Returns 0.0 if max_drawdown >= 0 or is zero

    Interpretation:
        Measures profit percentage per unit of drawdown percentage
        > 10: Exceptional - high profit with minimal drawdown
        5-10: Very good risk/reward
        2-5: Good performance
        < 2: High drawdown relative to profit
    """
    if max_drawdown >= 0 or abs(max_drawdown) == 0:
        return 0.0

    return net_profit_percentage / abs(max_drawdown)
