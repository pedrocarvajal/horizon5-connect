# Code reviewed on 2025-11-21 by Pedro Carvajal

from enums.order_side import OrderSide
from enums.order_type import OrderType
from services.gateway.models.gateway_leverage_info import GatewayLeverageInfoModel
from services.gateway.models.gateway_symbol_info import GatewaySymbolInfoModel
from services.gateway.models.gateway_trading_fees import GatewayTradingFeesModel
from tests.integration.binance.wrappers.binance import BinanceWrapper
from typing import Optional


class TestBinanceSymbol(BinanceWrapper):
    # ───────────────────────────────────────────────────────────
    # SETUP
    # ───────────────────────────────────────────────────────────
    def setUp(self) -> None:
        super().setUp()
        self._log.setup(name="test_binance_symbol")

    # ───────────────────────────────────────────────────────────
    # SYMBOL INFO TESTS
    # ───────────────────────────────────────────────────────────
    def test_get_symbol_info(self) -> None:
        """Test retrieving symbol information returns valid data."""
        symbol_info = self._gateway.get_symbol_info(symbol=self._SYMBOL)

        self._assert_symbol_info_is_valid(symbol_info=symbol_info)

    # ───────────────────────────────────────────────────────────
    # TRADING FEES TESTS
    # ───────────────────────────────────────────────────────────
    def test_get_trading_fees(self) -> None:
        """Test retrieving trading fees returns valid commission data."""
        trading_fees = self._gateway.get_trading_fees(symbol=self._SYMBOL)

        self._assert_trading_fees_is_valid(trading_fees=trading_fees)

    # ───────────────────────────────────────────────────────────
    # LEVERAGE TESTS
    # ───────────────────────────────────────────────────────────
    def test_get_leverage_info(self) -> None:
        """Test retrieving leverage information after opening a position."""
        order = self._gateway.place_order(
            symbol=self._SYMBOL,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            volume=self._DEFAULT_ORDER_VOLUME,
        )

        assert order is not None, "Order should not be None"
        assert order.id != "", "Order ID should not be empty"

        leverage_info = self._gateway.get_leverage_info(symbol=self._SYMBOL)

        self._assert_leverage_info_is_valid(leverage_info=leverage_info)

        self._close_position(symbol=self._SYMBOL, order=order)

    def test_set_leverage(self) -> None:
        """Test setting leverage for a symbol returns success."""
        result = self._gateway.set_leverage(symbol=self._SYMBOL, leverage=20)

        assert result is True, f"Set leverage should return True, got {result}"

    # ───────────────────────────────────────────────────────────
    # PRIVATE HELPERS
    # ───────────────────────────────────────────────────────────
    def _assert_symbol_info_is_valid(
        self,
        symbol_info,
        expected_symbol: Optional[str] = None,
    ) -> None:
        if expected_symbol is None:
            expected_symbol = self._SYMBOL

        assert symbol_info is not None, "Symbol info should not be None"
        assert isinstance(symbol_info, GatewaySymbolInfoModel), "Symbol info should be a GatewaySymbolInfoModel"
        assert symbol_info.symbol == expected_symbol, f"Symbol should be {expected_symbol}, got {symbol_info.symbol}"
        assert symbol_info.base_asset != "", f"Base asset should not be empty, got {symbol_info.base_asset}"
        assert symbol_info.quote_asset != "", f"Quote asset should not be empty, got {symbol_info.quote_asset}"
        assert (
            symbol_info.price_precision >= 0
        ), f"Price precision should be >= 0, got {symbol_info.price_precision}"
        assert (
            symbol_info.quantity_precision >= 0
        ), f"Quantity precision should be >= 0, got {symbol_info.quantity_precision}"
        assert symbol_info.response is not None, "Response should not be None"

    def _assert_trading_fees_is_valid(
        self,
        trading_fees,
        expected_symbol: Optional[str] = None,
    ) -> None:
        if expected_symbol is None:
            expected_symbol = self._SYMBOL

        assert trading_fees is not None, "Trading fees should not be None"
        assert isinstance(trading_fees, GatewayTradingFeesModel), "Trading fees should be a GatewayTradingFeesModel"
        assert trading_fees.symbol == expected_symbol, f"Symbol should be {expected_symbol}, got {trading_fees.symbol}"
        assert trading_fees.maker_commission is not None, "Maker commission should not be None"
        assert (
            trading_fees.maker_commission >= 0
        ), f"Maker commission should be >= 0, got {trading_fees.maker_commission}"
        assert trading_fees.taker_commission is not None, "Taker commission should not be None"
        assert (
            trading_fees.taker_commission >= 0
        ), f"Taker commission should be >= 0, got {trading_fees.taker_commission}"
        assert trading_fees.response is not None, "Response should not be None"

    def _assert_leverage_info_is_valid(
        self,
        leverage_info,
        expected_symbol: Optional[str] = None,
    ) -> None:
        if expected_symbol is None:
            expected_symbol = self._SYMBOL

        assert leverage_info is not None, "Leverage info should not be None"
        assert isinstance(leverage_info, GatewayLeverageInfoModel), "Leverage info should be a GatewayLeverageInfoModel"
        assert (
            leverage_info.symbol == expected_symbol
        ), f"Symbol should be {expected_symbol}, got {leverage_info.symbol}"
        assert leverage_info.leverage >= 1, f"Leverage should be >= 1, got {leverage_info.leverage}"
        assert leverage_info.response is not None, "Response should not be None"
