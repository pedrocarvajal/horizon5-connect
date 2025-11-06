from typing import List


def get_r2(values: List[float]) -> float:
    """
    Calculate R-squared (coefficient of determination) for linear trend.

    Args:
        values: List of performance values over time (e.g., cumulative returns)

    Returns:
        R² value between 0 and 1
        Returns 0.0 if insufficient data or no variance

    Interpretation:
        Measures how well a linear trend explains the data
        1.0 (100%): Perfect linear trend
        0.8-1.0: Strong linear trend
        0.5-0.8: Moderate trend
        0.0-0.5: Weak/no linear trend
        High R² = consistent, predictable growth
        Low R² = volatile, erratic performance
    """
    n = len(values)
    min_values = 2

    if n < min_values:
        return 0.0

    x = list(range(n))
    y = values

    mean_x = sum(x) / n
    mean_y = sum(y) / n

    numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    denominator_x = sum((x[i] - mean_x) ** 2 for i in range(n))

    if denominator_x == 0:
        return 0.0

    slope = numerator / denominator_x
    intercept = mean_y - slope * mean_x

    ss_res = sum((y[i] - (slope * x[i] + intercept)) ** 2 for i in range(n))
    ss_tot = sum((y[i] - mean_y) ** 2 for i in range(n))

    if ss_tot == 0:
        return 0.0

    return 1 - (ss_res / ss_tot)
