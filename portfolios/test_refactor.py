"""Test portfolio for backtest refactor validation."""

from assets.btcusdt import Asset as BTCUSDTAsset
from enums.asset_quality_method import AssetQualityMethod
from services.portfolio import PortfolioService


class Portfolio(PortfolioService):
    """Test portfolio for refactor validation."""

    _id = "test-refactor"
    _portfolio_quality_method = AssetQualityMethod.WEIGHTED_AVERAGE

    def __init__(self) -> None:
        """Initialize the test portfolio."""
        super().__init__()

        self.setup_assets()

    def setup_assets(self) -> None:
        """Configure portfolio with single BTCUSDT asset."""
        self._assets = [
            (BTCUSDTAsset, 200000.0),
        ]
