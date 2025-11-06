def get_calmar_ratio(
    cagr: float,
    max_drawdown: float,
) -> float:
    """
    Calculate Calmar Ratio (return to drawdown ratio).

    Args:
        cagr: Compound Annual Growth Rate as decimal
        max_drawdown: Maximum drawdown as negative decimal (e.g., -0.05 = -5%)

    Returns:
        Calmar Ratio as absolute value (CAGR / |max_drawdown|)
        Returns 0.0 if max_drawdown >= 0 or is zero

    Interpretation:
        Higher is better - more return per unit of drawdown risk
        > 3.0: Excellent risk-adjusted performance
        1.0-3.0: Good performance
        < 1.0: Poor risk-adjusted returns
    """
    if max_drawdown >= 0:
        return 0.0

    abs_max_drawdown = abs(max_drawdown)

    if abs_max_drawdown == 0:
        return 0.0

    return cagr / abs_max_drawdown
