"""Low-risk portfolio configuration with conservative asset allocation."""

from assets.btcusdt import Asset as BTCUSDTAsset
from assets.ethusdt import Asset as ETHUSDTAsset
from assets.solusdt import Asset as SOLUSDTAsset
from services.portfolio import PortfolioService


class Portfolio(PortfolioService):
    """Low-risk portfolio containing conservative trading strategies."""

    _id = "low-risk"

    def __init__(self) -> None:
        """Initialize the low-risk portfolio with configured assets."""
        super().__init__()

        self.setup_assets()

    def setup_assets(self) -> None:
        """Configure the portfolio assets for low-risk trading."""
        self._assets = [
            (BTCUSDTAsset, 100000.0),
            (ETHUSDTAsset, 100000.0),
            (SOLUSDTAsset, 100000.0),
        ]
