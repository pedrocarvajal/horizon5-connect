"""Integration tests for MetaAPI trade history operations."""

from vendor.enums.order_side import OrderSide
from vendor.services.gateway.models.gateway_trade import GatewayTradeModel
from vendor.tests.integration.metaapi.wrappers.metaapi import MetaApiWrapper


class TestMetaApiTrade(MetaApiWrapper):
    """Integration tests for MetaAPI trade history retrieval."""

    def setUp(self) -> None:
        super().setUp()

    def test_get_trades(self) -> None:
        """Test retrieving trade history."""
        trades = self._gateway.get_trades()
        assert trades is not None, "Trades should not be None"
        assert isinstance(trades, list), "Trades should be a list"
        assert all(isinstance(t, GatewayTradeModel) for t in trades), "All trades should be GatewayTradeModel"
        if len(trades) > 0:
            trade = trades[0]
            assert trade.id != "", "Trade ID should not be empty"
            assert trade.side in [OrderSide.BUY, OrderSide.SELL, None], "Side should be BUY, SELL, or None"
            assert trade.price >= 0, "Price should be >= 0"
            assert trade.volume >= 0, "Volume should be >= 0"
            assert trade.commission >= 0, "Commission should be >= 0"
            assert trade.response is not None, "Response should not be None"
            actual_trades = [t for t in trades if t.symbol != ""]
            if len(actual_trades) > 0:
                actual_trade = actual_trades[0]
                assert actual_trade.order_id != "", "Order ID should not be empty for real trades"
                assert actual_trade.symbol != "", "Symbol should not be empty for real trades"
        self._log.info(f"Total trades found: {len(trades)}")

    def test_get_trades_by_symbol(self) -> None:
        """Test retrieving trades filtered by symbol."""
        trades = self._gateway.get_trades(symbol=self._SYMBOL)
        assert trades is not None, "Trades should not be None"
        assert isinstance(trades, list), "Trades should be a list"
        assert all(isinstance(t, GatewayTradeModel) for t in trades), "Trades should be GatewayTradeModel"
        for trade in trades:
            assert trade.symbol.upper() == self._SYMBOL.upper(), f"Symbol should be {self._SYMBOL}"
        self._log.info(f"Total trades found for {self._SYMBOL}: {len(trades)}")
