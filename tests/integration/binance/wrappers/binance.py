"""Base wrapper for Binance integration tests."""

import unittest
from typing import Dict, Optional, Tuple

from enums.order_side import OrderSide
from enums.order_type import OrderType
from helpers.get_env import get_env
from services.gateway import GatewayService
from services.gateway.models.enums.gateway_order_status import GatewayOrderStatus
from services.gateway.models.gateway_order import GatewayOrderModel
from services.gateway.models.gateway_position import GatewayPositionModel
from services.logging import LoggingService


class BinanceWrapper(unittest.TestCase):
    """Base wrapper for Binance integration tests."""

    _SYMBOL: str = "BTCUSDT"
    _DEFAULT_ORDER_VOLUME: float = 0.002

    def __init__(self, method_name: str = "runTest") -> None:
        """
        Initialize the Binance wrapper.

        Args:
            method_name: Name of the test method to run.
        """
        super().__init__(method_name)
        self._gateway: GatewayService
        self._log: LoggingService
        self._verification: Optional[Dict[str, bool]]

    def setUp(self) -> None:
        """Set up the test environment."""
        self._log = LoggingService()
        self._validate_sandbox_configuration()
        self._gateway = GatewayService(gateway="binance", sandbox=True)
        self._verification = self._gateway.get_verification()
        assert self._gateway.sandbox is True, "Sandbox must be enabled for tests"
        assert self._verification is not None, "Verification should not be None"
        assert self._verification["credentials_configured"] is True, "Credentials should be configured"

    def _place_test_order(
        self, symbol: Optional[str] = None, side: OrderSide = OrderSide.BUY, volume: Optional[float] = None
    ) -> Optional[GatewayOrderModel]:
        if symbol is None:
            symbol = self._SYMBOL
        if volume is None:
            volume = self._DEFAULT_ORDER_VOLUME
        return self._gateway.place_order(symbol=symbol, side=side, order_type=OrderType.MARKET, volume=volume)

    def _delete_order_by_id(self, symbol: str, order_id: str) -> None:
        order = self._gateway.get_order(symbol=symbol, order_id=order_id)
        if not order:
            self._log.warning(f"Order {order_id} not found")
            return
        if order.status == GatewayOrderStatus.PENDING:
            self._cancel_order(symbol=symbol, order=order, order_id=order_id)
        elif order.status == GatewayOrderStatus.EXECUTED:
            self._close_position_for_order(symbol=symbol, order=order, order_id=order_id)
        else:
            self._log.info(f"Order {order_id} is already closed or cancelled")

    def _close_position(self, symbol: str, order: GatewayOrderModel) -> None:
        positions = self._gateway.get_positions(symbol=symbol)
        if len(positions) == 0:
            self._log.warning(f"No position found for order {order.id}")
            return
        position = positions[0]
        if position.volume == 0:
            self._log.info(f"No position to close for order {order.id}")
            return
        close_side, close_volume = self._compute_close_parameters(order=order, position=position)
        self._place_close_order(symbol=symbol, order=order, close_side=close_side, close_volume=close_volume)

    def _cancel_order(self, symbol: str, order: GatewayOrderModel, order_id: str) -> None:
        cancelled_order = self._gateway.cancel_order(symbol=symbol, order=order)
        assert cancelled_order is not None, f"Failed to cancel order {order_id}"
        self._log.info(f"Order {order_id} cancelled successfully")

    def _validate_sandbox_configuration(self) -> None:
        testnet_api_key = get_env("BINANCE_TESTNET_API_KEY")
        testnet_api_secret = get_env("BINANCE_TESTNET_API_SECRET")
        assert testnet_api_key is not None, (
            "BINANCE_TESTNET_API_KEY must be configured for tests. Set BINANCE_TESTNET_API_KEY in environment variables"
        )
        assert testnet_api_key != "", (
            "BINANCE_TESTNET_API_KEY must not be empty. Set BINANCE_TESTNET_API_KEY in environment variables"
        )
        assert testnet_api_secret is not None, (
            "BINANCE_TESTNET_API_SECRET must be configured for tests. "
            "Set BINANCE_TESTNET_API_SECRET in environment variables"
        )
        assert testnet_api_secret != "", (
            "BINANCE_TESTNET_API_SECRET must not be empty. Set BINANCE_TESTNET_API_SECRET in environment variables"
        )

    def _compute_close_parameters(
        self, order: GatewayOrderModel, position: GatewayPositionModel
    ) -> Tuple[OrderSide, float]:
        close_side = OrderSide.SELL if order.side and order.side.is_buy() else OrderSide.BUY
        close_volume = abs(position.volume)
        return (close_side, close_volume)

    def _place_close_order(
        self, symbol: str, order: GatewayOrderModel, close_side: OrderSide, close_volume: float
    ) -> None:
        close_order = self._gateway.place_order(
            symbol=symbol, side=close_side, order_type=OrderType.MARKET, volume=close_volume
        )
        assert close_order is not None, f"Failed to close position for order {order.id}"
        self._log.info(f"Position closed for order {order.id}")

    def _close_position_for_order(self, symbol: str, order: GatewayOrderModel, order_id: str) -> None:
        positions = self._gateway.get_positions(symbol=symbol)
        assert len(positions) > 0, f"No position found for order {order_id}"
        position = positions[0]
        assert position.volume != 0, f"No position to close for order {order_id}"
        close_side, close_volume = self._compute_close_parameters(order=order, position=position)
        self._place_close_order(symbol=symbol, order=order, close_side=close_side, close_volume=close_volume)
