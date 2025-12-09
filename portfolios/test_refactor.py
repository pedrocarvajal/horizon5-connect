"""Test portfolio for backtest refactor validation."""

from assets.btcusdt import Asset as BTCUSDTAsset
from assets.ethusdt import Asset as ETHUSDTAsset
from enums.asset_quality_method import AssetQualityMethod
from services.portfolio import PortfolioService


class Portfolio(PortfolioService):
    """Test portfolio with 2 assets for refactor validation."""

    _id = "test-refactor"
    _portfolio_quality_method = AssetQualityMethod.WEIGHTED_AVERAGE

    def __init__(self) -> None:
        """Initialize the test portfolio."""
        super().__init__()

        self.setup_assets()

    def setup_assets(self) -> None:
        """Configure portfolio with 2 assets."""
        self._assets = [
            (BTCUSDTAsset, 100000.0),
            (ETHUSDTAsset, 100000.0),
        ]
