"""Calculate Information Ratio for benchmark comparison."""


def get_information_ratio(alpha: float, tracking_error: float) -> float:
    """Calculate Information Ratio - risk-adjusted alpha.

    Information ratio measures the quality of alpha generated relative
    to the tracking error (risk taken to generate that alpha).
    Formula: IR = Alpha / TrackingError

    Args:
        alpha: Jensen's Alpha (excess return).
        tracking_error: Standard deviation of excess returns.

    Returns:
        Information ratio (0.0 if tracking error is zero).
    """
    if tracking_error == 0:
        return 0.0

    return alpha / tracking_error
