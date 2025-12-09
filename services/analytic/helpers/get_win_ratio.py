"""Calculate Win Ratio (ratio of winning trades to total trades)."""

from typing import List


def get_win_ratio(trades_profits: List[float]) -> float:
    """
    Calculate Win Ratio (ratio of winning trades to total trades).

    Args:
        trades_profits: List of individual trade P&L values (positive and negative)

    Returns:
        Win Ratio as decimal (0-1)
        Returns 0.0 if no trades

    Interpretation:
        > 0.60: Good win rate
        0.50-0.60: Average win rate
        0.40-0.50: Below average, needs good risk/reward
        < 0.40: Low win rate, requires high profit factor
    """
    if len(trades_profits) == 0:
        return 0.0

    winning_trades = sum(1 for profit in trades_profits if profit > 0)
    total_trades = len(trades_profits)

    return winning_trades / total_trades
