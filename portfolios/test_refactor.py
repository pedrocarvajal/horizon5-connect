"""Test portfolio for backtest refactor validation."""

from assets.btcusdt import Asset as BTCUSDTAsset
from vendor.enums.asset_quality_method import AssetQualityMethod
from vendor.services.portfolio import PortfolioService


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
            {"asset": BTCUSDTAsset, "allocation": 200000.0, "enabled": True},
        ]
