# Last coding review: 2025-11-18 12:30:00

from enums.order_side import OrderSide
from enums.order_type import OrderType
from services.gateway.models.gateway_leverage_info import GatewayLeverageInfoModel
from services.gateway.models.gateway_symbol_info import GatewaySymbolInfoModel
from services.gateway.models.gateway_trading_fees import GatewayTradingFeesModel
from tests.integration.binance.wrappers.binance import BinanceWrapper


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

    def test_get_trading_fees(self) -> None:
        self._log.info("Getting trading fees for BTCUSDT")

        trading_fees = self._gateway.get_trading_fees(symbol="BTCUSDT")

        assert trading_fees is not None, "Trading fees should not be None"
        assert isinstance(trading_fees, GatewayTradingFeesModel), "Trading fees should be a GatewayTradingFeesModel"
        assert trading_fees.symbol != "", f"Symbol should not be empty, got {trading_fees.symbol}"
        assert trading_fees.maker_commission is not None, "Maker commission should not be None"
        assert trading_fees.maker_commission >= 0, f"Maker commission, got {trading_fees.maker_commission}"
        assert trading_fees.taker_commission is not None, "Taker commission should not be None"
        assert trading_fees.taker_commission >= 0, f"Taker commission, got {trading_fees.taker_commission}"
        assert trading_fees.response is not None, "Response should not be None"

    def test_get_leverage_info(self) -> None:
        self._log.info("Opening position to get leverage info for BTCUSDT")

        symbol = "BTCUSDT"
        volume = 0.002

        order = self._gateway.place_order(
            symbol=symbol,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            volume=volume,
        )

        assert order is not None, "Order should not be None"
        assert order.id != "", "Order ID should not be empty"
        self._log.info(f"Position opened with order {order.id}")

        leverage_info = self._gateway.get_leverage_info(symbol=symbol)

        assert leverage_info is not None, "Leverage info should not be None"
        assert isinstance(leverage_info, GatewayLeverageInfoModel), "Leverage info should be a GatewayLeverageInfoModel"
        assert leverage_info.symbol != "", f"Symbol should not be empty, got {leverage_info.symbol}"
        assert leverage_info.leverage >= 1, f"Leverage, got {leverage_info.leverage}"
        assert leverage_info.response is not None, "Response should not be None"

        self._log.info(f"Closing position for order {order.id}")
        self._close_position(symbol=symbol, order=order)

    def test_set_leverage(self) -> None:
        self._log.info("Setting leverage to 20x for BTCUSDT")

        result = self._gateway.set_leverage(symbol="BTCUSDT", leverage=20)

        assert result is True, f"Set leverage should return True, got {result}"
