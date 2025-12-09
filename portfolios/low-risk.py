"""Low-risk portfolio configuration with conservative asset allocation."""

from assets.bnbusdt import Asset as BNBUSDTAsset
from assets.btcusdt import Asset as BTCUSDTAsset
from assets.ethusdt import Asset as ETHUSDTAsset
from assets.solusdt import Asset as SOLUSDTAsset
from assets.xrpusdt import Asset as XRPUSDTAsset
from enums.asset_quality_method import AssetQualityMethod
from services.portfolio import PortfolioService


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
            (BNBUSDTAsset, 200000.0),
            (BTCUSDTAsset, 200000.0),
            (ETHUSDTAsset, 200000.0),
            (SOLUSDTAsset, 200000.0),
            (XRPUSDTAsset, 200000.0),
        ]
