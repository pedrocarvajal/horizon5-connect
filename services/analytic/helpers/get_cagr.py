def get_cagr(
    initial_nav: float,
    final_nav: float,
    elapsed_days: int,
) -> float:
    """
    Calculate Compound Annual Growth Rate (CAGR).

    Args:
        initial_nav: Starting Net Asset Value (must be positive)
        final_nav: Ending Net Asset Value
        elapsed_days: Number of days between initial and final NAV

    Returns:
        CAGR as a decimal (e.g., 0.0865 = 8.65% annual growth)
        Returns 0.0 if elapsed_days < 1 or initial_nav <= 0
        Returns -1.0 if final_nav <= 0 (total loss)

    Interpretation:
        Positive: Portfolio grew at X% per year
        Zero: No growth
        Negative: Portfolio declined at X% per year
        Values > 0.15 (15%) are considered excellent
        Values < 0 indicate losses
    """
    min_days = 1
    days_per_year = 365

    if elapsed_days < min_days or initial_nav <= 0:
        return 0.0

    if final_nav <= 0:
        return -1.0

    nav_ratio = final_nav / initial_nav
    years_fraction = days_per_year / elapsed_days

    return (nav_ratio**years_fraction) - 1
