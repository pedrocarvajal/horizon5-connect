# Last coding review: 2025-11-18 12:30:00

from services.gateway.models.gateway_symbol_info import GatewaySymbolInfoModel
from tests.integration.wrappers.binance import BinanceWrapper


class TestBinanceSymbol(BinanceWrapper):
    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def setUp(self) -> None:
        super().setUp()
        self._log.setup(name="test_binance_symbol")

    def test_get_symbol_info(self) -> None:
        self._log.info("Getting symbol information for BTCUSDT")

        symbol_info = self._gateway.get_symbol_info(symbol="BTCUSDT")

        assert symbol_info is not None, "Symbol info should not be None"
        assert isinstance(symbol_info, GatewaySymbolInfoModel), "Symbol info should be a GatewaySymbolInfoModel"
        assert symbol_info.symbol != "", f"Symbol should not be empty, got {symbol_info.symbol}"
        assert symbol_info.base_asset != "", f"Base asset should not be empty, got {symbol_info.base_asset}"
        assert symbol_info.quote_asset != "", f"Quote asset should not be empty, got {symbol_info.quote_asset}"
        assert symbol_info.price_precision >= 0, f"Price precision, got {symbol_info.price_precision}"
        assert symbol_info.quantity_precision >= 0, f"Quantity precision, got {symbol_info.quantity_precision}"
        assert symbol_info.response is not None, "Response should not be None"

        self._log.debug(symbol_info.model_dump())
