"""Low-risk portfolio configuration with conservative asset allocation."""

from assets.btcusdt import Asset as BTCUSDTAsset
from assets.xauusd import Asset as XAUUSDAsset
from vendor.enums.asset_quality_method import AssetQualityMethod
from vendor.services.portfolio import PortfolioService


class Portfolio(PortfolioService):
    """Low-risk portfolio containing conservative trading strategies."""

    _id = "low-risk"
    _portfolio_quality_method = AssetQualityMethod.WEIGHTED_AVERAGE

    def __init__(self) -> None:
        """Initialize the low-risk portfolio with configured assets."""
        super().__init__()

        self.setup_assets()

    def setup_assets(self) -> None:
        """Configure the portfolio assets for low-risk trading."""
        self._assets = [
            {
                "asset": BTCUSDTAsset,
                "allocation": 100_000,
                "enabled": False,
            },
            {
                "asset": XAUUSDAsset,
                "allocation": 100_000,
                "enabled": True,
            },
        ]
