def get_recovery_factor(net_profit: float, max_drawdown: float) -> float:
    """
    Calculate Recovery Factor (net profit to maximum drawdown ratio).

    Args:
        net_profit: Total net profit/loss (final NAV - initial NAV)
        max_drawdown: Maximum drawdown as negative decimal

    Returns:
        Recovery Factor as ratio (net_profit / |max_drawdown|)
        Returns 0.0 if max_drawdown >= 0 or is zero

    Interpretation:
        Measures profit generated per unit of drawdown risk
        > 10: Exceptional - high profit with minimal drawdown
        5-10: Very good risk/reward
        2-5: Good performance
        < 2: High drawdown relative to profit
    """
    if max_drawdown >= 0 or abs(max_drawdown) == 0:
        return 0.0

    return net_profit / abs(max_drawdown)
