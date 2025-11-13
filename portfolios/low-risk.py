from assets.btcusdt import Asset as BTCUSDTAsset
from services.portfolio import PortfolioService


class Portfolio(PortfolioService):
    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(self) -> None:
        super().__init__()

        self.setup_assets()

    def setup_assets(self) -> None:
        self._assets = [
            BTCUSDTAsset,
        ]
