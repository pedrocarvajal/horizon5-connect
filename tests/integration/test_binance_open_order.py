import unittest

from enums.order_side import OrderSide
from enums.order_type import OrderType
from services.gateway import GatewayService
from services.logging import LoggingService


class TestBinanceOpenOrder(unittest.TestCase):
    _log: LoggingService

    def setUp(self) -> None:
        self._log = LoggingService()
        self._log.setup("test_binance_open_order")

    def test_open_market_order_minimum_lot(self) -> None:
        gateway = GatewayService(
            "binance",
            futures=True,
        )

        leverage = 3
        volume = 0.01

        self._log.info(f"Setting leverage to {leverage}x for BTCUSDT")

        leverage_set = gateway.set_leverage(
            symbol="btcusdt",
            leverage=leverage,
        )

        assert leverage_set, "Leverage should be set successfully"
        self._log.info(f"Opening order with minimum volume: {volume} BTC")

        order = gateway.open(
            symbol="btcusdt",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            volume=volume,
        )

        if order is None:
            self._log.warning(
                "Order creation failed. This may be due to insufficient margin. "
                "Please ensure your Binance account has sufficient balance."
            )

            self.fail(
                "Order should be created. Check account balance and margin requirements."
            )

        assert order.symbol == "BTCUSDT", "Symbol should match"
        assert order.side == OrderSide.BUY, "Side should be BUY"
        assert order.order_type == OrderType.MARKET, "Order type should be MARKET"
        assert order.volume == volume, f"Volume should be {volume}"
        assert order.status is not None, "Status should be set"

        self._log.info(f"Order created successfully: {order.id}")
        self._log.info(f"Order status: {order.status.value}")
        self._log.info(f"Order volume: {order.volume}")
        self._log.info(f"Order executed volume: {order.executed_volume}")

        self._log.warning(
            f"IMPORTANT: Order {order.id} is now OPEN. "
            f"Please close this order manually or wait for the user to close it."
        )
