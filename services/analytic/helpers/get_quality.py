"""Calculate quality score for backtest evaluation."""

from typing import Any, Dict, Optional, Tuple

from enums.quality_method import QualityMethod
from models.backtest_expectation import (
    DEFAULT_BACKTEST_EXPECTATION,
    BacktestExpectationModel,
)


def get_quality(
    method: QualityMethod = QualityMethod.FQS,
    expectations: Optional[BacktestExpectationModel] = None,
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

    Args:
        method: QualityMethod enum specifying the calculation method.
        expectations: BacktestExpectationModel with [min, expected] ranges.
            If None, uses DEFAULT_BACKTEST_EXPECTATION.
        **metrics: All available metrics from the backtest:
            - sortino_ratio: Risk-adjusted return (downside volatility only)
            - sharpe_ratio: Risk-adjusted return (total volatility)
            - r_squared: Linear trend coefficient of equity curve (0 to 1)
            - max_drawdown: Maximum peak-to-trough decline (negative value)
            - profit_factor: Sum of winning trades / sum of losing trades
            - num_trades: Total number of closed trades
            - cagr: Compound annual growth rate
            - calmar_ratio: CAGR / max_drawdown
            - recovery_factor: Performance / max_drawdown
            - performance_percentage: Total return as percentage

    Returns:
        Tuple of (quality_score, method_name).
        Score is normalized to [0, 1] range for all methods.
    """
    exp = expectations or DEFAULT_BACKTEST_EXPECTATION

    if method == QualityMethod.FQS:
        return _calculate_fqs(metrics, exp)

    if method == QualityMethod.SORTINO:
        return _calculate_single_metric(metrics, exp, "sortino_ratio", "sortino")

    if method == QualityMethod.DRAWDOWN:
        return _calculate_single_metric(metrics, exp, "max_drawdown", "drawdown", higher_is_better=False)

    if method == QualityMethod.PERFORMANCE:
        return _calculate_single_metric(metrics, exp, "performance_percentage", "performance")

    if method == QualityMethod.PROFIT_FACTOR:
        return _calculate_single_metric(metrics, exp, "profit_factor", "profit_factor")

    if method == QualityMethod.SHARPE:
        return _calculate_single_metric(metrics, exp, "sharpe_ratio", "sharpe")

    if method == QualityMethod.R_SQUARED:
        return _calculate_single_metric(metrics, exp, "r_squared", "r_squared")

    return _calculate_fqs(metrics, exp)


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
) -> Tuple[float, str]:
    """Calculate Final Quality Score (FQS) using weighted average.

    Weights:
        - num_trades: 0.10 (statistical significance)
        - max_drawdown: 0.20 (risk management)
        - performance_percentage: 0.15 (returns)
        - sortino_ratio: 0.20 (risk-adjusted returns)
        - profit_factor: 0.15 (trade efficiency)
        - r_squared: 0.10 (consistency)
        - sharpe_ratio: 0.10 (risk-adjusted returns alternative)

    Returns:
        Tuple of (quality_score, "fqs").
    """
    metric_weights = {
        "num_trades": 0.10,
        "max_drawdown": 0.20,
        "performance_percentage": 0.15,
        "sortino_ratio": 0.20,
        "profit_factor": 0.15,
        "r_squared": 0.10,
        "sharpe_ratio": 0.10,
    }

    lower_is_better_metrics = {"max_drawdown"}

    total_weight = 0.0
    weighted_sum = 0.0

    for metric_key, weight in metric_weights.items():
        exp_range = expectations.get_range(metric_key)
        if exp_range is None:
            continue

        current_value = metrics.get(metric_key, 0)
        threshold, expected = exp_range
        higher_is_better = metric_key not in lower_is_better_metrics

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
