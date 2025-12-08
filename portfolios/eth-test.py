"""Test portfolio for ETHUSDT parameter optimization."""

from assets.ethusdt import Asset as ETHUSDTAsset
from services.portfolio import PortfolioService


class Portfolio(PortfolioService):
    """Test portfolio for ETHUSDT optimization."""

    _id = "eth-test"

    def __init__(self) -> None:
        """Initialize the test portfolio."""
        super().__init__()

        self.setup_assets()

    def setup_assets(self) -> None:
        """Configure ETHUSDT asset for testing."""
        self._assets = [
            (ETHUSDTAsset, 100000.0),
        ]
