"""Calculate prop firm compliance metrics."""

from typing import List, NamedTuple


class PropfirmMetrics(NamedTuple):
    """Prop firm compliance metrics container."""

    best_day_profit: float
    best_day_profit_ratio: float
    max_daily_loss: float
    max_daily_profit: float
    daily_loss_breach_count: int
    trading_days: int
    daily_loss_compliant: bool
    overall_loss_compliant: bool
    consistency_compliant: bool
    trading_days_compliant: bool


DAILY_LOSS_LIMIT = -0.05
OVERALL_LOSS_LIMIT = -0.10
CONSISTENCY_LIMIT = 0.30
MIN_TRADING_DAYS = 4


def get_propfirm_metrics(
    daily_profits: List[float],
    initial_balance: float,
    max_drawdown: float,
) -> PropfirmMetrics:
    """
    Calculate prop firm compliance metrics.

    Based on common prop firm rules (FTMO, FundedNext, Topstep, etc.):
    - Daily loss limit: 5% of initial balance
    - Overall loss limit: 10% of initial balance
    - Consistency rule: Best day profit <= 30% of total profit
    - Minimum trading days: 4 days with activity

    Args:
        daily_profits: List of daily profit values (in currency units)
        initial_balance: Starting balance for ratio calculations
        max_drawdown: Maximum drawdown as negative ratio (e.g., -0.08 for 8%)

    Returns:
        PropfirmMetrics with all compliance indicators

    Interpretation:
        All compliant flags True = Ready for prop firm evaluation
        Any False = Needs adjustment before prop firm attempt
    """
    if len(daily_profits) == 0 or initial_balance <= 0:
        return PropfirmMetrics(
            best_day_profit=0.0,
            best_day_profit_ratio=0.0,
            max_daily_loss=0.0,
            max_daily_profit=0.0,
            daily_loss_breach_count=0,
            trading_days=0,
            daily_loss_compliant=True,
            overall_loss_compliant=True,
            consistency_compliant=True,
            trading_days_compliant=False,
        )

    daily_profit_ratios = [p / initial_balance for p in daily_profits]

    max_daily_profit_ratio = max(daily_profit_ratios) if daily_profit_ratios else 0.0
    min_daily_profit_ratio = min(daily_profit_ratios) if daily_profit_ratios else 0.0

    max_daily_profit = max(daily_profits)
    best_day_profit = max_daily_profit

    total_profit = sum(daily_profits)
    best_day_profit_ratio = best_day_profit / total_profit if total_profit > 0 else 0.0

    daily_loss_breach_count = sum(1 for ratio in daily_profit_ratios if ratio < DAILY_LOSS_LIMIT)

    trading_days = sum(1 for p in daily_profits if p != 0)

    daily_loss_compliant = min_daily_profit_ratio >= DAILY_LOSS_LIMIT
    overall_loss_compliant = max_drawdown >= OVERALL_LOSS_LIMIT
    consistency_compliant = best_day_profit_ratio <= CONSISTENCY_LIMIT if total_profit > 0 else True
    trading_days_compliant = trading_days >= MIN_TRADING_DAYS

    return PropfirmMetrics(
        best_day_profit=best_day_profit,
        best_day_profit_ratio=best_day_profit_ratio,
        max_daily_loss=min_daily_profit_ratio,
        max_daily_profit=max_daily_profit_ratio,
        daily_loss_breach_count=daily_loss_breach_count,
        trading_days=trading_days,
        daily_loss_compliant=daily_loss_compliant,
        overall_loss_compliant=overall_loss_compliant,
        consistency_compliant=consistency_compliant,
        trading_days_compliant=trading_days_compliant,
    )
