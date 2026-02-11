"""Bitcoin portfolio configuration."""

from vendor.services.portfolio import PortfolioService


class Portfolio(PortfolioService):
    """Bitcoin-only portfolio with Binance gateway."""

    def __init__(self) -> None:
        """Initialize Bitcoin portfolio."""
        super().__init__(
            name="Bitcoin",
            assets=["assets.btcusdt"],
            allocation=100_000,
        )
