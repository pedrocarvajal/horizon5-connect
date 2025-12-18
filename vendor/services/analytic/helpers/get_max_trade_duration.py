"""Calculate maximum trade duration in minutes."""

from typing import List


def get_max_trade_duration(trade_durations_minutes: List[float]) -> float:
    """
    Calculate maximum trade duration in minutes.

    Args:
        trade_durations_minutes: List of trade durations in minutes

    Returns:
        Maximum duration in minutes
        Returns 0.0 if no trades

    Interpretation:
        < 60: Scalping/short-term trades
        60-240: Intraday trades
        240-1440: Swing trades (4h to 1 day)
        > 1440: Position trades (multi-day)
    """
    if len(trade_durations_minutes) == 0:
        return 0.0

    return max(trade_durations_minutes)
