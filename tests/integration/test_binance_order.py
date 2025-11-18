# Last coding review: 2025-11-18 13:55:00

from enums.order_side import OrderSide
from enums.order_type import OrderType
from services.gateway.models.gateway_order import GatewayOrderModel
from tests.integration.wrappers.binance import BinanceWrapper


class TestBinanceOrder(BinanceWrapper):
    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def setUp(self) -> None:
        super().setUp()
        self._log.setup(name="test_binance_order")

    def test_place_order_market(self) -> None:
        self._log.info("Placing a market BUY order for BTCUSDT")

        order = self._gateway.place_order(
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            volume=0.002,
        )

        assert order is not None, "Order should not be None"
        assert isinstance(order, GatewayOrderModel), "Order should be a GatewayOrderModel"
        assert order.id != "", "Order ID should not be empty"
        assert order.symbol == "BTCUSDT", "Symbol should be BTCUSDT"
        assert order.side == OrderSide.BUY, "Side should be BUY"
        assert order.order_type == OrderType.MARKET, "Order type should be MARKET"
        assert order.volume > 0, "Volume should be > 0"
        assert order.executed_volume >= 0, "Executed volume should be >= 0"
        assert order.response is not None, "Response should not be None"

        self._log.info(f"Order placed successfully: {order.id}")
        self._log.debug(order.model_dump(mode="json"))
