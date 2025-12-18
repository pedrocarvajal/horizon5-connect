"""Calculate overnight trading metrics."""

import datetime
from typing import List, Tuple


def get_overnight_metrics(
    trade_timestamps: List[Tuple[datetime.datetime, datetime.datetime]],
) -> Tuple[int, float]:
    """
    Calculate overnight trading metrics.

    A trade is considered overnight if it was open across midnight
    (i.e., opened on one day and closed on a different day).

    Args:
        trade_timestamps: List of (created_at, updated_at) tuples for each trade

    Returns:
        Tuple of (overnight_count, overnight_ratio)
        - overnight_count: Number of trades held overnight
        - overnight_ratio: Ratio of overnight trades vs total (0-1)

    Interpretation:
        overnight_ratio close to 0: Mostly intraday trading
        overnight_ratio close to 1: Mostly swing/position trading

    Prop firm relevance:
        Some prop firms (e.g., Topstep) prohibit overnight holding.
        Higher overnight_ratio may disqualify from certain programs.
    """
    if len(trade_timestamps) == 0:
        return 0, 0.0

    overnight_count = 0

    for created_at, updated_at in trade_timestamps:
        if created_at.date() != updated_at.date():
            overnight_count += 1

    total_trades = len(trade_timestamps)
    overnight_ratio = overnight_count / total_trades if total_trades > 0 else 0.0

    return overnight_count, overnight_ratio
