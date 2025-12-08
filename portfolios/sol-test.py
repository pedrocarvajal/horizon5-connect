"""Test portfolio for SOLUSDT parameter optimization."""

from assets.solusdt import Asset as SOLUSDTAsset
from services.portfolio import PortfolioService


class Portfolio(PortfolioService):
    """Test portfolio for SOLUSDT optimization."""

    _id = "sol-test"

    def __init__(self) -> None:
        """Initialize the test portfolio."""
        super().__init__()

        self.setup_assets()

    def setup_assets(self) -> None:
        """Configure SOLUSDT asset for testing."""
        self._assets = [
            (SOLUSDTAsset, 100000.0),
        ]
