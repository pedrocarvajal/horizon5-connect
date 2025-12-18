"""Calculate prop firm readiness quality score."""


def get_quality_propfirm(
    consistency_ratio: float,
    max_daily_loss: float,
    max_drawdown: float,
    profit_factor: float,
    trading_days: int,
) -> float:
    """
    Calculate quality score for prop firm readiness.

    Uses weighted average of key prop firm metrics:
    - Consistency (25%): Best day profit ratio (lower is better)
    - Daily loss control (25%): Max daily loss (less negative is better)
    - Drawdown control (20%): Max drawdown (less negative is better)
    - Profitability (15%): Profit factor (higher is better)
    - Activity (15%): Trading days (more is better)

    Args:
        consistency_ratio: Best day profit as ratio of total profit (0-1+)
        max_daily_loss: Worst daily loss as ratio (-1 to 0)
        max_drawdown: Max drawdown as ratio (-1 to 0)
        profit_factor: Profit factor (0+)
        trading_days: Number of active trading days

    Returns:
        Quality score between 0 and 1
        - 0.8+: Excellent prop firm readiness
        - 0.6-0.8: Good, minor adjustments needed
        - 0.4-0.6: Fair, significant improvements needed
        - <0.4: Poor, major changes required

    Thresholds based on FTMO/FundedNext/Topstep requirements.
    """
    weights = {
        "consistency": 0.25,
        "daily_loss": 0.25,
        "drawdown": 0.20,
        "profit_factor": 0.15,
        "trading_days": 0.15,
    }

    consistency_score = _calculate_consistency_score(consistency_ratio)
    daily_loss_score = _calculate_daily_loss_score(max_daily_loss)
    drawdown_score = _calculate_drawdown_score(max_drawdown)
    profit_factor_score = _calculate_profit_factor_score(profit_factor)
    trading_days_score = _calculate_trading_days_score(trading_days)

    weighted_sum = (
        consistency_score * weights["consistency"]
        + daily_loss_score * weights["daily_loss"]
        + drawdown_score * weights["drawdown"]
        + profit_factor_score * weights["profit_factor"]
        + trading_days_score * weights["trading_days"]
    )

    return round(weighted_sum, 4)


def _calculate_consistency_score(consistency_ratio: float) -> float:
    """
    Score consistency ratio (lower is better).

    Thresholds:
        <= 0.20: Perfect (1.0)
        >= 0.50: Failing (0.0)
    """
    threshold = 0.50
    expected = 0.20

    if consistency_ratio <= expected:
        return 1.0
    if consistency_ratio >= threshold:
        return 0.0

    return (threshold - consistency_ratio) / (threshold - expected)


def _calculate_daily_loss_score(max_daily_loss: float) -> float:
    """
    Score max daily loss (less negative is better).

    Thresholds:
        >= -0.02: Perfect (1.0)
        <= -0.05: Failing (0.0) - prop firm limit
    """
    threshold = -0.05
    expected = -0.02

    if max_daily_loss >= expected:
        return 1.0
    if max_daily_loss <= threshold:
        return 0.0

    return (max_daily_loss - threshold) / (expected - threshold)


def _calculate_drawdown_score(max_drawdown: float) -> float:
    """
    Score max drawdown (less negative is better).

    Thresholds:
        >= -0.05: Perfect (1.0)
        <= -0.10: Failing (0.0) - prop firm limit
    """
    threshold = -0.10
    expected = -0.05

    if max_drawdown >= expected:
        return 1.0
    if max_drawdown <= threshold:
        return 0.0

    return (max_drawdown - threshold) / (expected - threshold)


def _calculate_profit_factor_score(profit_factor: float) -> float:
    """
    Score profit factor (higher is better).

    Thresholds:
        >= 2.0: Perfect (1.0)
        <= 1.0: Failing (0.0)
    """
    threshold = 1.0
    expected = 2.0

    if profit_factor >= expected:
        return 1.0
    if profit_factor <= threshold:
        return 0.0

    return (profit_factor - threshold) / (expected - threshold)


def _calculate_trading_days_score(trading_days: int) -> float:
    """
    Score trading days (more is better).

    Thresholds:
        >= 10: Perfect (1.0)
        <= 1: Failing (0.0)
        4: Minimum prop firm requirement (0.33)
    """
    threshold = 1
    expected = 10

    if trading_days >= expected:
        return 1.0
    if trading_days <= threshold:
        return 0.0

    return (trading_days - threshold) / (expected - threshold)
