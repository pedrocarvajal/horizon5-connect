"""Calculate quality score for backtest evaluation."""

from typing import Any, Dict, Optional, Tuple

from vendor.enums.quality_method import QualityMethod
from vendor.models.backtest_expectation import BacktestExpectationModel

DAYS_IN_YEAR = 365


def _annualize_performance(performance_percentage: float, days_elapsed: int) -> float:
    """Annualize performance percentage based on elapsed days.

    Formula: (1 + performance) ^ (365 / days) - 1

    Args:
        performance_percentage: Raw performance as decimal (e.g., 0.25 for 25%)
        days_elapsed: Number of days in the backtest period

    Returns:
        Annualized performance as decimal.
        Returns 0.0 if days_elapsed <= 0.

    Examples:
        - 25% in 90 days → (1.25)^(365/90) - 1 = 166% annualized
        - 50% in 180 days → (1.50)^(365/180) - 1 = 125% annualized
        - 100% in 365 days → (2.00)^(365/365) - 1 = 100% annualized
    """
    if days_elapsed <= 0:
        return 0.0

    if performance_percentage <= -1:
        return -1.0

    return (1 + performance_percentage) ** (DAYS_IN_YEAR / days_elapsed) - 1


def get_quality(
    method: QualityMethod = QualityMethod.FQS,
    expectations: Optional[BacktestExpectationModel] = None,
    days_elapsed: int = 0,
    **metrics: Any,
) -> Tuple[float, str]:
    """Calculate quality score for a backtest using the specified method.

    Each metric is evaluated against its [min, expected] range:
    - Value < min → quality contribution = 0
    - Value >= expected → quality contribution = 1
    - Value between min and expected → linearly interpolated (0-1)

    For inverted metrics (like max_drawdown where lower is better):
    - Value <= expected → quality contribution = 1
    - Value >= min → quality contribution = 0

    Note: performance_percentage is automatically annualized using days_elapsed
    before comparison with thresholds.

    Args:
        method: QualityMethod enum specifying the calculation method.
        expectations: BacktestExpectationModel with [min, expected] ranges.
            If None, uses DEFAULT_BACKTEST_EXPECTATION.
        days_elapsed: Number of days in the backtest period for annualization.
        **metrics: All available metrics from the backtest:
            - r_squared: Linear trend coefficient of equity curve (0 to 1)
            - max_drawdown: Maximum peak-to-trough decline (negative value)
            - profit_factor: Sum of winning trades / sum of losing trades
            - num_trades: Total number of closed trades
            - recovery_factor: Performance / max_drawdown
            - win_ratio: Ratio of winning trades (0-1)
            - trade_duration: Average trade duration in minutes
            - performance_percentage: Total return as percentage (will be annualized)

    Returns:
        Tuple of (quality_score, method_name).
        Score is normalized to [0, 1] range for all methods.
    """
    exp = expectations or BacktestExpectationModel.default()

    if method == QualityMethod.FQS:
        return _calculate_fqs(metrics, exp, days_elapsed)

    if method == QualityMethod.DRAWDOWN:
        return _calculate_single_metric(metrics, exp, "max_drawdown", "drawdown", higher_is_better=False)

    if method == QualityMethod.PROFIT_FACTOR:
        return _calculate_single_metric(metrics, exp, "profit_factor", "profit_factor")

    if method == QualityMethod.R_SQUARED:
        return _calculate_single_metric(metrics, exp, "r_squared", "r_squared")

    if method == QualityMethod.WIN_RATIO:
        return _calculate_single_metric(metrics, exp, "win_ratio", "win_ratio")

    return _calculate_fqs(metrics, exp, days_elapsed)


def _calculate_metric_quality(
    current_value: float,
    expected_value: float,
    threshold_value: float,
    higher_is_better: bool = True,
) -> float:
    """Calculate quality score for a metric using linear interpolation.

    Args:
        current_value: The actual metric value.
        expected_value: The target value (quality = 1 at or beyond this).
        threshold_value: The minimum acceptable value (quality = 0 at or beyond this).
        higher_is_better: If True, higher values are better. If False, lower values are better.

    Returns:
        Normalized score between 0 and 1.

    Examples:
        Higher is better (sortino_ratio):
            - threshold=0.5, expected=2.0
            - value=2.5 → 1.0 (exceeds expected)
            - value=1.25 → 0.5 (midpoint)
            - value=0.3 → 0.0 (below threshold)

        Lower is better (max_drawdown as positive percentage):
            - threshold=0.25, expected=0.10
            - value=0.05 → 1.0 (better than expected)
            - value=0.10 → 1.0 (at expected)
            - value=0.175 → 0.5 (midpoint)
            - value=0.30 → 0.0 (worse than threshold)
    """
    if higher_is_better:
        if current_value < threshold_value:
            return 0.0
        if current_value >= expected_value:
            return 1.0
        return (current_value - threshold_value) / (expected_value - threshold_value)

    if current_value > threshold_value:
        return 0.0
    if current_value <= expected_value:
        return 1.0
    return (threshold_value - current_value) / (threshold_value - expected_value)


def _calculate_single_metric(
    metrics: Dict[str, Any],
    expectations: BacktestExpectationModel,
    metric_key: str,
    method_name: str,
    higher_is_better: bool = True,
) -> Tuple[float, str]:
    """Calculate quality based on a single metric.

    Args:
        metrics: Dictionary of all metrics.
        expectations: BacktestExpectationModel with ranges.
        metric_key: Key of the metric in metrics dict.
        method_name: Name to return as the method.
        higher_is_better: If True, higher values are better.

    Returns:
        Tuple of (quality_score, method_name).
    """
    current_value = metrics.get(metric_key, 0)
    exp_range = expectations.get_range(metric_key)

    if exp_range is None:
        return 0.5, method_name

    threshold, expected = exp_range

    if not higher_is_better:
        current_value = abs(current_value)
        threshold = abs(threshold)
        expected = abs(expected)

    score = _calculate_metric_quality(current_value, expected, threshold, higher_is_better)
    return round(score, 4), method_name


def _calculate_fqs(
    metrics: Dict[str, Any],
    expectations: BacktestExpectationModel,
    days_elapsed: int = 0,
) -> Tuple[float, str]:
    """Calculate Final Quality Score (FQS) using weighted average.

    FQS focuses on three core metrics:
        - performance_percentage: 0.40 (returns, annualized)
        - max_drawdown: 0.40 (risk management)
        - r_squared: 0.20 (consistency/equity curve linearity)

    Note: performance_percentage is annualized before comparison.

    Args:
        metrics: Dictionary of all metrics.
        expectations: BacktestExpectationModel with ranges.
        days_elapsed: Number of days in the backtest period for annualization.

    Returns:
        Tuple of (quality_score, "fqs").
    """
    metric_weights = {
        "performance_percentage": 0.40,
        "max_drawdown": 0.40,
        "r_squared": 0.20,
    }

    lower_is_better_metrics = {"max_drawdown"}
    annualized_metrics = {"performance_percentage"}

    total_weight = 0.0
    weighted_sum = 0.0

    for metric_key, weight in metric_weights.items():
        exp_range = expectations.get_range(metric_key)
        if exp_range is None:
            continue

        current_value = metrics.get(metric_key, 0)
        threshold, expected = exp_range
        higher_is_better = metric_key not in lower_is_better_metrics

        if metric_key in annualized_metrics and days_elapsed > 0:
            current_value = _annualize_performance(current_value, days_elapsed)

        if metric_key in lower_is_better_metrics:
            current_value = abs(current_value)
            threshold = abs(threshold)
            expected = abs(expected)

        score = _calculate_metric_quality(current_value, expected, threshold, higher_is_better)
        weighted_sum += score * weight
        total_weight += weight

    if total_weight == 0:
        return 0.0, "fqs"

    final_score = weighted_sum / total_weight
    return round(final_score, 4), "fqs"
