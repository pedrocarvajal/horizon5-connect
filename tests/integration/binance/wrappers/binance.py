import datetime
import unittest
from typing import Dict, Optional

from configs.timezone import TIMEZONE
from enums.order_side import OrderSide
from enums.order_type import OrderType
from models.order import OrderModel
from services.gateway import GatewayService
from services.gateway.models.enums.gateway_order_status import GatewayOrderStatus
from services.gateway.models.gateway_order import GatewayOrderModel
from services.logging import LoggingService


class BinanceWrapper(unittest.TestCase):
    _gateway: GatewayService
    _log: LoggingService
    _verification: Dict[str, bool]

    def setUp(self) -> None:
        self._log = LoggingService()
        self._log.setup(name=self.__class__.__name__)

        self._gateway = GatewayService(
            gateway="binance",
        )

        self._verification = self._gateway.get_verification()

        assert self._gateway.sandbox is True, "Sandbox must be enabled for tests"
        assert self._verification is not None, "Verification should not be None"
        assert self._verification["credentials_configured"] is True, "Credentials should be configured"

    def _open_test_order(
        self,
        symbol: str = "BTCUSDT",
        side: OrderSide = OrderSide.BUY,
        volume: float = 0.002,
        price: Optional[float] = None,
    ) -> Optional[GatewayOrderModel]:
        order_type = OrderType.MARKET if price is None else OrderType.LIMIT

        return self._gateway.place_order(
            symbol=symbol,
            side=side,
            order_type=order_type,
            volume=volume,
            price=price,
        )

    def _create_test_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        volume: float,
        price: float = 0.0,
        backtest: bool = False,
    ) -> OrderModel:
        """Create a test OrderModel instance for testing.

        Args:
            symbol: Trading symbol (e.g., "BTCUSDT").
            side: Order side (BUY or SELL).
            order_type: Order type (MARKET, LIMIT, etc.).
            volume: Order volume.
            price: Order price (default: 0.0).
            backtest: Whether order is for backtest mode (default: False).

        Returns:
            OrderModel instance configured with provided parameters.
        """
        return OrderModel(
            symbol=symbol,
            side=side,
            order_type=order_type,
            volume=volume,
            price=price,
            backtest=backtest,
            gateway=self._gateway,
            created_at=datetime.datetime.now(tz=TIMEZONE),
            updated_at=datetime.datetime.now(tz=TIMEZONE),
        )

    def _close_order_by_id(
        self,
        symbol: str,
        order_id: str,
    ) -> None:
        order = self._gateway.get_order(
            symbol=symbol,
            order_id=order_id,
        )

        if not order:
            self._log.warning(f"Order {order_id} not found")
            return

        if order.status == GatewayOrderStatus.PENDING:
            self._cancel_pending_order(
                symbol=symbol,
                order=order,
                order_id=order_id,
            )

        elif order.status == GatewayOrderStatus.EXECUTED:
            self._close_executed_order_position(
                symbol=symbol,
                order=order,
                order_id=order_id,
            )

        else:
            self._log.info(f"Order {order_id} is already closed or cancelled")

    def _close_position(
        self,
        symbol: str,
        order: GatewayOrderModel,
    ) -> None:
        positions = self._gateway.get_positions(symbol=symbol)

        if len(positions) == 0:
            self._log.warning(f"No position found for order {order.id}")
            return

        position = positions[0]

        if position.volume == 0:
            self._log.info(f"No position to close for order {order.id}")
            return

        close_side = OrderSide.SELL if order.side and order.side.is_buy() else OrderSide.BUY
        close_volume = abs(position.volume)

        close_order = self._gateway.place_order(
            symbol=symbol,
            side=close_side,
            order_type=OrderType.MARKET,
            volume=close_volume,
        )

        assert close_order is not None, f"Failed to close position for order {order.id}"
        self._log.info(f"Position closed for order {order.id}")

    def _cancel_pending_order(
        self,
        symbol: str,
        order: GatewayOrderModel,
        order_id: str,
    ) -> None:
        cancelled_order = self._gateway.cancel_order(
            symbol=symbol,
            order=order,
        )

        assert cancelled_order is not None, f"Failed to cancel order {order_id}"
        self._log.info(f"Order {order_id} cancelled successfully")

    def _close_executed_order_position(
        self,
        symbol: str,
        order: GatewayOrderModel,
        order_id: str,
    ) -> None:
        positions = self._gateway.get_positions(symbol=symbol)

        assert len(positions) > 0, f"No position found for order {order_id}"

        position = positions[0]

        assert position.volume != 0, f"No position to close for order {order_id}"

        close_side = OrderSide.SELL if order.side and order.side.is_buy() else OrderSide.BUY
        close_volume = abs(position.volume)

        close_order = self._gateway.place_order(
            symbol=symbol,
            side=close_side,
            order_type=OrderType.MARKET,
            volume=close_volume,
        )

        assert close_order is not None, f"Failed to close position for order {order_id}"
        self._log.info(f"Position closed for order {order_id}")
