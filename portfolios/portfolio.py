from assets.btcusdt import Asset as BTCUSDTAsset
from models.backtest_settings import (
    BacktestCommissionProfileBySymbolModel,
    BacktestSettingsModel,
)
from services.portfolio import PortfolioService


class Portfolio(PortfolioService):
    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(self) -> None:
        super().__init__()

        self.setup_assets()
        self.setup_backtest()

    def setup_assets(self) -> None:
        self._assets = [
            BTCUSDTAsset,
        ]

    def setup_backtest(self) -> None:
        super().setup_backtest()

        self._backtest_settings = BacktestSettingsModel(
            commission_by_symbols=[
                BacktestCommissionProfileBySymbolModel(
                    symbol="btcusdt",
                    buy_rate=0.001,
                    sell_rate=0.001,
                ),
            ],
        )
