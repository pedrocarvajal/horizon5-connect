# Code reviewed on 2025-11-21 by Pedro Carvajal

from enums.order_side import OrderSide
from services.gateway.models.gateway_trade import GatewayTradeModel
from tests.integration.binance.wrappers.binance import BinanceWrapper


class TestBinanceTrade(BinanceWrapper):
    # ───────────────────────────────────────────────────────────
    # SETUP
    # ───────────────────────────────────────────────────────────
    def setUp(self) -> None:
        super().setUp()
        self._log.setup(name="test_binance_trade")

    # ───────────────────────────────────────────────────────────
    # TRADE TESTS
    # ───────────────────────────────────────────────────────────
    def test_get_trades(self) -> None:
        """Test retrieving all trades from the gateway without filtering."""
        trades = self._gateway.get_trades()

        assert trades is not None, "Trades should not be None"
        assert isinstance(trades, list), "Trades should be a list"
        assert all(isinstance(t, GatewayTradeModel) for t in trades), "All trades should be GatewayTradeModel"

        if len(trades) > 0:
            trade = trades[0]
            assert trade.id != "", "Trade ID should not be empty"
            assert trade.order_id != "", "Order ID should not be empty"
            assert trade.symbol != "", "Symbol should not be empty"
            assert trade.side in [OrderSide.BUY, OrderSide.SELL, None], "Side should be BUY, SELL, or None"
            assert trade.price >= 0, "Price should be >= 0"
            assert trade.volume >= 0, "Volume should be >= 0"
            assert trade.commission >= 0, "Commission should be >= 0"
            assert trade.response is not None, "Response should not be None"

    def test_get_trades_by_symbol(self) -> None:
        """Test retrieving trades filtered by a specific symbol."""
        trades = self._gateway.get_trades(symbol=self._SYMBOL)

        assert trades is not None, "Trades should not be None"
        assert isinstance(trades, list), "Trades should be a list"
        assert all(isinstance(t, GatewayTradeModel) for t in trades), "Trades should be GatewayTradeModel"

        for trade in trades:
            assert trade.symbol == self._SYMBOL, f"Symbol should be {self._SYMBOL}"
