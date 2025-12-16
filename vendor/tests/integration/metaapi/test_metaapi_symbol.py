"""Integration tests for MetaAPI symbol operations."""

from vendor.services.gateway.models.gateway_leverage_info import GatewayLeverageInfoModel
from vendor.services.gateway.models.gateway_symbol_info import GatewaySymbolInfoModel
from vendor.services.gateway.models.gateway_trading_fees import GatewayTradingFeesModel
from vendor.tests.integration.metaapi.wrappers.metaapi import MetaApiWrapper


class TestMetaApiSymbol(MetaApiWrapper):
    """Integration tests for MetaAPI symbol information retrieval."""

    def setUp(self) -> None:
        super().setUp()

    def test_get_symbol_info(self) -> None:
        """Test retrieving symbol specification."""
        symbol_info = self._gateway.get_symbol_info(symbol=self._SYMBOL)
        assert symbol_info is not None, "Symbol info should not be None"
        assert isinstance(symbol_info, GatewaySymbolInfoModel), "Should be GatewaySymbolInfoModel"
        assert symbol_info.symbol.upper() == self._SYMBOL.upper(), f"Symbol should be {self._SYMBOL}"
        assert symbol_info.price_precision >= 0, "Price precision should be >= 0"
        assert symbol_info.quantity_precision >= 0, "Quantity precision should be >= 0"
        assert symbol_info.response is not None, "Response should not be None"
        self._log.info(f"Symbol: {symbol_info.symbol}, tick={symbol_info.tick_size}, step={symbol_info.step_size}")

    def test_get_leverage_info(self) -> None:
        """Test retrieving leverage information."""
        leverage_info = self._gateway.get_leverage_info(symbol=self._SYMBOL)
        assert leverage_info is not None, "Leverage info should not be None"
        assert isinstance(leverage_info, GatewayLeverageInfoModel), "Should be GatewayLeverageInfoModel"
        assert leverage_info.symbol.upper() == self._SYMBOL.upper(), f"Symbol should be {self._SYMBOL}"
        assert leverage_info.leverage >= 1, "Leverage should be >= 1"
        assert leverage_info.response is not None, "Response should not be None"
        self._log.info(f"Leverage for {self._SYMBOL}: {leverage_info.leverage}x")

    def test_get_trading_fees(self) -> None:
        """Test retrieving trading fees."""
        fees = self._gateway.get_trading_fees(symbol=self._SYMBOL)
        assert fees is not None, "Fees should not be None"
        assert isinstance(fees, GatewayTradingFeesModel), "Should be GatewayTradingFeesModel"
        assert fees.symbol.upper() == self._SYMBOL.upper(), f"Symbol should be {self._SYMBOL}"
        self._log.info(f"Trading fees for {self._SYMBOL}: maker={fees.maker_commission}, taker={fees.taker_commission}")
