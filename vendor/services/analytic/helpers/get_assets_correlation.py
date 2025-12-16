"""Calculate average pairwise correlation between portfolio assets."""

from typing import Dict, List

from vendor.services.analytic.helpers.get_correlation import get_correlation

MIN_ASSETS_FOR_CORRELATION: int = 2


def get_assets_correlation(assets_returns: Dict[str, List[float]]) -> float:
    """Calculate average pairwise Pearson correlation between portfolio assets.

    Computes the correlation between each pair of assets' returns and returns
    the average. This metric indicates how diversified the portfolio is:
    - Values close to 1: Assets move together (low diversification)
    - Values close to 0: Assets are uncorrelated (good diversification)
    - Values close to -1: Assets move opposite (high diversification benefit)

    Args:
        assets_returns: Dictionary mapping asset IDs to their lists of daily returns.
                       Each asset should have the same number of return values.

    Returns:
        Average pairwise correlation (-1 to 1). Returns 0.0 if less than 2 assets.
    """
    asset_ids = list(assets_returns.keys())
    number_of_assets = len(asset_ids)

    if number_of_assets < MIN_ASSETS_FOR_CORRELATION:
        return 0.0

    correlations: List[float] = []

    for i in range(number_of_assets):
        for j in range(i + 1, number_of_assets):
            asset_a_returns = assets_returns[asset_ids[i]]
            asset_b_returns = assets_returns[asset_ids[j]]

            correlation = get_correlation(asset_a_returns, asset_b_returns)
            correlations.append(correlation)

    if not correlations:
        return 0.0

    average_correlation = sum(correlations) / len(correlations)
    return round(average_correlation, 4)
