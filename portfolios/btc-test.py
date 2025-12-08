"""Test portfolio for BTCUSDT parameter optimization."""

from assets.btcusdt import Asset as BTCUSDTAsset
from services.portfolio import PortfolioService


class Portfolio(PortfolioService):
    """Test portfolio for BTCUSDT optimization."""

    _id = "btc-test"

    def __init__(self) -> None:
        """Initialize the test portfolio."""
        super().__init__()

        self.setup_assets()

    def setup_assets(self) -> None:
        """Configure BTCUSDT asset for testing."""
        self._assets = [
            (BTCUSDTAsset, 100000.0),
        ]
