from typing import List


def get_profit_factor(trades_profits: List[float]) -> float:
    """
    Calculate Profit Factor (ratio of gross profits to gross losses).

    Args:
        trades_profits: List of individual trade P&L values (positive and negative)

    Returns:
        Profit Factor as ratio (total_wins / total_losses)
        Returns 0.0 if no trades or no losses

    Interpretation:
        > 2.0: Excellent - wins are twice the size of losses
        1.5-2.0: Good trading performance
        1.0-1.5: Marginally profitable
        < 1.0: Losing strategy (more losses than wins)
        = 1.0: Break-even
    """
    if len(trades_profits) == 0:
        return 0.0

    total_wins = sum(profit for profit in trades_profits if profit > 0)
    total_losses = abs(sum(profit for profit in trades_profits if profit < 0))

    if total_losses == 0:
        return 0.0

    return total_wins / total_losses

