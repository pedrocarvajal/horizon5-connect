"""Low-risk portfolio configuration with conservative asset allocation."""

from vendor.services.portfolio import PortfolioService


class Portfolio(PortfolioService):
    """Low-risk portfolio containing conservative trading strategies."""

    def __init__(self) -> None:
        """Initialize the low-risk portfolio with configured assets."""
        super().__init__(name="Low Risk", assets=["assets.xauusd", "assets.ndx"], allocation=100_000)
