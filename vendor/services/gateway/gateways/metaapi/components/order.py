"""MetaAPI order component for order management operations."""

from typing import Any, Dict, List, Optional

from vendor.enums.order_side import OrderSide
from vendor.enums.order_type import OrderType
from vendor.helpers.parse_optional_float import parse_optional_float
from vendor.services.gateway.gateways.metaapi.components.base import BaseComponent
from vendor.services.gateway.models.enums.gateway_order_status import GatewayOrderStatus
from vendor.services.gateway.models.gateway_order import GatewayOrderModel


class OrderComponent(BaseComponent):
    """
    Component for handling MetaAPI order-related operations.

    Provides methods to place, cancel, and retrieve orders on MetaTrader
    via MetaAPI. Handles order validation and adaptation of MetaAPI responses
    to internal order models matching the Binance gateway response format.
    """

    def place_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        volume: float,
        price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        client_order_id: Optional[str] = None,
    ) -> Optional[GatewayOrderModel]:
        """
        Place a new order on MetaTrader via MetaAPI.

        Args:
            symbol: Trading symbol (e.g., "XAUUSD").
            side: Order side (BUY or SELL).
            order_type: Order type (MARKET).
            volume: Order volume/quantity in lots.
            price: Optional price (ignored for MARKET orders).
            stop_loss: Optional stop loss price.
            take_profit: Optional take profit price.
            client_order_id: Optional custom client order ID.

        Returns:
            GatewayOrderModel if order was placed successfully, None otherwise.
        """
        if not self._validate_place_order_params(
            symbol=symbol,
            side=side,
            order_type=order_type,
            volume=volume,
        ):
            return None

        if not self._config.account_id:
            self._log.error(
                "account_id required for place_order",
            )
            return None

        action_type = self._get_action_type(side=side, order_type=order_type)

        if not action_type:
            self._log.error(
                "Unsupported order type",
                order_type=order_type,
            )
            return None

        if price and order_type == OrderType.MARKET:
            self._log.warning("Price parameter is ignored for MARKET orders")

        trade_body: Dict[str, Any] = {
            "actionType": action_type,
            "symbol": symbol.upper(),
            "volume": volume,
        }

        if stop_loss:
            trade_body["stopLoss"] = stop_loss

        if take_profit:
            trade_body["takeProfit"] = take_profit

        if client_order_id:
            trade_body["clientId"] = client_order_id

        endpoint = f"/users/current/accounts/{self._config.account_id}/trade"

        response = self._execute(
            method="POST",
            endpoint=endpoint,
            json_body=trade_body,
            use_client_api=True,
        )

        if not response:
            return None

        if not isinstance(response, dict):
            self._log.error(
                "Unexpected response type for trade",
                response_type=type(response).__name__,
            )
            return None

        return self._adapt_trade_response(
            response=response,
            symbol=symbol.upper(),
            side=side,
            order_type=order_type,
            volume=volume,
        )

    def cancel_order(
        self,
        order: GatewayOrderModel,
    ) -> Optional[GatewayOrderModel]:
        """
        Cancel an existing pending order on MetaTrader via MetaAPI.

        Args:
            order: GatewayOrderModel instance containing the order to cancel.

        Returns:
            GatewayOrderModel with updated status if cancellation was successful,
            None otherwise.
        """
        if not self._validate_order(order=order):
            return None

        if not self._config.account_id:
            self._log.error(
                "account_id required for cancel_order",
            )
            return None

        trade_body: Dict[str, Any] = {
            "actionType": "ORDER_CANCEL",
            "orderId": order.id,
        }

        endpoint = f"/users/current/accounts/{self._config.account_id}/trade"

        response = self._execute(
            method="POST",
            endpoint=endpoint,
            json_body=trade_body,
            use_client_api=True,
        )

        if not response:
            return None

        if not isinstance(response, dict):
            self._log.error(
                "Unexpected response type for cancel",
                response_type=type(response).__name__,
            )
            return None

        string_code = response.get("stringCode", "")

        if string_code in ["TRADE_RETCODE_DONE", "ERR_NO_ERROR"]:
            return GatewayOrderModel(
                id=order.id,
                symbol=order.symbol,
                side=order.side,
                order_type=order.order_type,
                status=GatewayOrderStatus.CANCELLED,
                volume=order.volume,
                executed_volume=order.executed_volume,
                price=order.price,
                response=response,
            )

        self._log.error(
            "Failed to cancel order",
            error_message=response.get("message", "Unknown error"),
        )
        return None

    def get_order(
        self,
        order_id: str,
    ) -> Optional[GatewayOrderModel]:
        """
        Retrieve a single pending order by ID from MetaAPI.

        Args:
            order_id: Order ID/ticket to retrieve.

        Returns:
            GatewayOrderModel if order was found, None otherwise.
        """
        if not self._config.account_id:
            self._log.error(
                "account_id required for get_order",
            )
            return None

        if not order_id:
            self._log.error(
                "order_id is required",
            )
            return None

        endpoint = f"/users/current/accounts/{self._config.account_id}/orders/{order_id}"

        response = self._execute(
            method="GET",
            endpoint=endpoint,
            use_client_api=True,
        )

        if not response:
            return None

        if not isinstance(response, dict):
            self._log.error(
                "Unexpected response type for order",
                response_type=type(response).__name__,
            )
            return None

        return self._adapt_order_response(response=response)

    def get_orders(
        self,
        symbol: Optional[str] = None,
    ) -> List[GatewayOrderModel]:
        """
        Retrieve pending orders from MetaAPI.

        Args:
            symbol: Optional trading symbol to filter orders.

        Returns:
            List of GatewayOrderModel instances. Empty list if request fails
            or no pending orders exist.
        """
        if not self._config.account_id:
            self._log.error(
                "account_id required for get_orders",
            )
            return []

        endpoint = f"/users/current/accounts/{self._config.account_id}/orders"

        response = self._execute(
            method="GET",
            endpoint=endpoint,
            use_client_api=True,
        )

        if not response:
            return []

        if not isinstance(response, list):
            self._log.error(
                "Unexpected response type for orders",
                response_type=type(response).__name__,
            )
            return []

        orders = self._adapt_orders_batch(response=response)

        if symbol:
            return [o for o in orders if o.symbol.upper() == symbol.upper()]

        return orders

    def modify_position(
        self,
        position_id: str,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
    ) -> bool:
        """
        Modify stop loss and/or take profit of an existing position.

        Args:
            position_id: Position ID to modify.
            stop_loss: New stop loss price (None to keep current).
            take_profit: New take profit price (None to keep current).

        Returns:
            True if modification was successful, False otherwise.
        """
        if not self._config.account_id:
            self._log.error(
                "account_id required for modify_position",
            )
            return False

        if not position_id:
            self._log.error(
                "position_id is required",
            )
            return False

        if stop_loss is None and take_profit is None:
            self._log.error(
                "At least one of stop_loss or take_profit is required",
            )
            return False

        trade_body: Dict[str, Any] = {
            "actionType": "POSITION_MODIFY",
            "positionId": position_id,
        }

        if stop_loss is not None:
            trade_body["stopLoss"] = stop_loss

        if take_profit is not None:
            trade_body["takeProfit"] = take_profit

        endpoint = f"/users/current/accounts/{self._config.account_id}/trade"

        response = self._execute(
            method="POST",
            endpoint=endpoint,
            json_body=trade_body,
            use_client_api=True,
        )

        if not response:
            return False

        if not isinstance(response, dict):
            self._log.error(
                "Unexpected response type for modify",
                response_type=type(response).__name__,
            )
            return False

        string_code = response.get("stringCode", "")

        if string_code in ["TRADE_RETCODE_DONE", "ERR_NO_ERROR"]:
            return True

        self._log.error(
            "Failed to modify position",
            error_message=response.get("message", "Unknown error"),
            code=string_code,
        )
        return False

    def close_position(
        self,
        position_id: str,
        volume: Optional[float] = None,
    ) -> Optional[GatewayOrderModel]:
        """
        Close a position on MetaTrader via MetaAPI.

        Args:
            position_id: Position ID to close.
            volume: Optional volume to close (partial close). If None, closes entire position.

        Returns:
            GatewayOrderModel representing the close order if successful, None otherwise.
        """
        if not self._config.account_id:
            self._log.error(
                "account_id required for close_position",
            )
            return None

        if not position_id:
            self._log.error(
                "position_id is required",
            )
            return None

        if volume is not None:
            trade_body: Dict[str, Any] = {
                "actionType": "POSITION_PARTIAL",
                "positionId": position_id,
                "volume": volume,
            }
        else:
            trade_body = {
                "actionType": "POSITION_CLOSE_ID",
                "positionId": position_id,
            }

        endpoint = f"/users/current/accounts/{self._config.account_id}/trade"

        response = self._execute(
            method="POST",
            endpoint=endpoint,
            json_body=trade_body,
            use_client_api=True,
        )

        if not response:
            return None

        if not isinstance(response, dict):
            self._log.error(
                "Unexpected response type for close",
                response_type=type(response).__name__,
            )
            return None

        string_code = response.get("stringCode", "")

        if string_code in ["TRADE_RETCODE_DONE", "TRADE_RETCODE_DONE_PARTIAL", "ERR_NO_ERROR"]:
            return GatewayOrderModel(
                id=str(response.get("orderId", "")),
                symbol="",
                side=None,
                order_type=OrderType.MARKET,
                status=GatewayOrderStatus.EXECUTED,
                volume=volume or 0.0,
                executed_volume=volume or 0.0,
                price=0.0,
                response=response,
            )

        self._log.error(
            "Failed to close position",
            error_message=response.get("message", "Unknown error"),
        )
        return None

    def _adapt_order_response(
        self,
        response: Dict[str, Any],
    ) -> Optional[GatewayOrderModel]:
        """
        Adapt MetaAPI order response to GatewayOrderModel.

        Args:
            response: Raw API response dictionary from MetaAPI.

        Returns:
            GatewayOrderModel instance with adapted data, or None if invalid.
        """
        if not response:
            return None

        order_id = str(response.get("id", ""))
        symbol = response.get("symbol", "").upper()
        order_type_str = response.get("type", "")
        state_str = response.get("state", "")
        volume = parse_optional_float(value=response.get("volume", 0))
        current_volume = parse_optional_float(value=response.get("currentVolume", 0))
        open_price = parse_optional_float(value=response.get("openPrice", 0))

        side = self._adapt_order_side(order_type_str=order_type_str)
        order_type = self._adapt_order_type(order_type_str=order_type_str)
        status = self._adapt_order_status(state_str=state_str)

        executed_volume = (volume or 0.0) - (current_volume or 0.0)

        return GatewayOrderModel(
            id=order_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            status=status,
            volume=volume or 0.0,
            executed_volume=max(executed_volume, 0.0),
            price=open_price or 0.0,
            response=response,
        )

    def _adapt_orders_batch(
        self,
        response: List[Dict[str, Any]],
    ) -> List[GatewayOrderModel]:
        """
        Adapt a batch of MetaAPI order responses to GatewayOrderModel list.

        Args:
            response: List of raw API response dictionaries.

        Returns:
            List of GatewayOrderModel instances.
        """
        orders: List[GatewayOrderModel] = []

        if not response:
            return orders

        for order_data in response:
            adapted_order = self._adapt_order_response(response=order_data)

            if adapted_order:
                orders.append(adapted_order)

        return orders

    def _adapt_order_side(
        self,
        order_type_str: str,
    ) -> Optional[OrderSide]:
        """
        Extract order side from MetaAPI order type string.

        Args:
            order_type_str: MetaAPI order type (e.g., ORDER_TYPE_BUY_LIMIT).

        Returns:
            OrderSide.BUY or OrderSide.SELL, or None if unknown.
        """
        if "BUY" in order_type_str:
            return OrderSide.BUY

        if "SELL" in order_type_str:
            return OrderSide.SELL

        return None

    def _adapt_order_type(
        self,
        order_type_str: str,
    ) -> OrderType:
        """
        Adapt MetaAPI order type to internal OrderType enum.

        Args:
            order_type_str: MetaAPI order type string.

        Returns:
            OrderType enum value (currently only MARKET supported).
        """
        if order_type_str and "MARKET" not in order_type_str.upper():
            self._log.warning(
                "Non-MARKET order type detected, treating as MARKET",
                order_type=order_type_str,
            )

        return OrderType.MARKET

    def _adapt_order_status(
        self,
        state_str: str,
    ) -> GatewayOrderStatus:
        """
        Adapt MetaAPI order state to GatewayOrderStatus enum.

        Args:
            state_str: MetaAPI order state string.

        Returns:
            GatewayOrderStatus enum value.
        """
        status_map = {
            "ORDER_STATE_STARTED": GatewayOrderStatus.PENDING,
            "ORDER_STATE_PLACED": GatewayOrderStatus.PENDING,
            "ORDER_STATE_CANCELED": GatewayOrderStatus.CANCELLED,
            "ORDER_STATE_PARTIAL": GatewayOrderStatus.PENDING,
            "ORDER_STATE_FILLED": GatewayOrderStatus.EXECUTED,
            "ORDER_STATE_REJECTED": GatewayOrderStatus.CANCELLED,
            "ORDER_STATE_EXPIRED": GatewayOrderStatus.CANCELLED,
            "ORDER_STATE_REQUEST_ADD": GatewayOrderStatus.PENDING,
            "ORDER_STATE_REQUEST_MODIFY": GatewayOrderStatus.PENDING,
            "ORDER_STATE_REQUEST_CANCEL": GatewayOrderStatus.CANCELLED,
        }

        return status_map.get(state_str, GatewayOrderStatus.PENDING)

    def _adapt_trade_response(
        self,
        response: Dict[str, Any],
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        volume: float,
    ) -> Optional[GatewayOrderModel]:
        """
        Adapt MetaAPI trade response to GatewayOrderModel.

        Args:
            response: Raw trade response from MetaAPI.
            symbol: Trading symbol.
            side: Order side.
            order_type: Order type.
            volume: Order volume.

        Returns:
            GatewayOrderModel if trade was successful, None otherwise.
        """
        string_code = response.get("stringCode", "")
        message = response.get("message", "")

        success_codes = [
            "TRADE_RETCODE_DONE",
            "TRADE_RETCODE_DONE_PARTIAL",
            "TRADE_RETCODE_PLACED",
            "ERR_NO_ERROR",
        ]

        if string_code not in success_codes:
            self._log.error(
                "Trade failed",
                error_message=message,
                code=string_code,
            )
            return None

        order_id = str(response.get("orderId", ""))
        position_id = response.get("positionId")

        status = GatewayOrderStatus.EXECUTED
        if string_code == "TRADE_RETCODE_PLACED":
            status = GatewayOrderStatus.PENDING

        return GatewayOrderModel(
            id=order_id or str(position_id or ""),
            symbol=symbol,
            side=side,
            order_type=order_type,
            status=status,
            volume=volume,
            executed_volume=volume if status == GatewayOrderStatus.EXECUTED else 0.0,
            price=0.0,
            response=response,
        )

    def _get_action_type(
        self,
        side: OrderSide,
        order_type: OrderType,
    ) -> Optional[str]:
        """
        Get MetaAPI action type from order side and type.

        Args:
            side: Order side.
            order_type: Order type.

        Returns:
            MetaAPI action type string, or None if unsupported.
        """
        if order_type == OrderType.MARKET:
            return "ORDER_TYPE_BUY" if side == OrderSide.BUY else "ORDER_TYPE_SELL"

        return None

    def _validate_order(
        self,
        order: GatewayOrderModel,
    ) -> bool:
        """
        Validate that order parameter is a valid GatewayOrderModel with an ID.

        Args:
            order: Order to validate.

        Returns:
            True if order is valid, False otherwise.
        """
        if not order:
            self._log.error(
                "order is required",
            )
            return False

        if not order.id:
            self._log.error(
                "order.id is required",
            )
            return False

        return True

    def _validate_place_order_params(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        volume: float,
    ) -> bool:
        """
        Validate all parameters for place_order method.

        Args:
            symbol: Trading symbol.
            side: Order side enum.
            order_type: Order type enum.
            volume: Order volume.

        Returns:
            True if all parameters are valid, False otherwise.
        """
        if not symbol:
            self._log.error(
                "symbol is required",
            )
            return False

        if not side:
            self._log.error(
                "side is required",
            )
            return False

        if not order_type:
            self._log.error(
                "order_type is required",
            )
            return False

        if volume <= 0:
            self._log.error(
                "volume must be greater than 0",
            )
            return False

        return True
