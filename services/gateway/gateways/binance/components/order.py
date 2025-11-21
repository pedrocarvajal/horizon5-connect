# Code reviewed on 2025-11-19 by pedrocarvajal

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from enums.order_side import OrderSide
from enums.order_type import OrderType
from helpers.parse import parse_optional_float, parse_timestamp_ms
from services.gateway.gateways.binance.components.base import BaseComponent
from services.gateway.gateways.binance.components.symbol import SymbolComponent
from services.gateway.gateways.binance.enums.binance_order_status import BinanceOrderStatus
from services.gateway.gateways.binance.models.config import BinanceConfigModel
from services.gateway.helpers import has_api_error
from services.gateway.models.enums.gateway_order_status import GatewayOrderStatus
from services.gateway.models.gateway_order import GatewayOrderModel


class OrderComponent(BaseComponent):
    """
    Component for handling Binance order-related operations.

    Provides methods to place, cancel, modify, and retrieve orders on Binance Futures.
    Handles order validation, volume calculation, and adaptation of Binance API responses
    to internal order models. Supports both market and limit orders with proper validation
    of symbol constraints, volume limits, and price requirements.

    Attributes:
        _MAX_ORDERS_QUERY_DAYS: Maximum number of days to query in a single request (7 days).
        _symbol_component: Component for symbol-related operations and symbol info retrieval.
    """

    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    _MAX_ORDERS_QUERY_DAYS = 7
    _symbol_component: SymbolComponent

    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(
        self,
        config: BinanceConfigModel,
    ) -> None:
        """
        Initialize the order component.

        Args:
            config: Binance configuration model containing API credentials and URLs.
        """
        super().__init__(config)

        self._symbol_component = SymbolComponent(
            config=config,
        )

    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def place_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        volume: float,
        price: Optional[float] = None,
        client_order_id: Optional[str] = None,
    ) -> Optional[GatewayOrderModel]:
        """
        Place a new order on Binance Futures.

        Creates and submits an order to Binance Futures API. Validates all parameters,
        calculates proper volume based on symbol constraints, and handles both market and
        limit order types. Returns the created order model or None if the order fails.

        Args:
            symbol: Trading pair symbol (e.g., "BTCUSDT").
            side: Order side (BUY or SELL).
            order_type: Order type (MARKET or LIMIT).
            volume: Order volume/quantity.
            price: Optional price for LIMIT orders. Required for LIMIT orders, ignored for MARKET orders.
            client_order_id: Optional custom client order ID for tracking.

        Returns:
            GatewayOrderModel if order was placed successfully, None otherwise.

        Example:
            >>> component = OrderComponent(config, symbol_component)
            >>> order = component.place_order(
            ...     symbol="BTCUSDT",
            ...     side=OrderSide.BUY,
            ...     order_type=OrderType.MARKET,
            ...     volume=0.001
            ... )
            >>> if order:
            ...     print(f"Order placed: {order.id}")
        """
        if not self._validate_place_order_params(
            symbol=symbol,
            side=side,
            order_type=order_type,
            volume=volume,
            price=price,
        ):
            return None

        quantity = self._get_volume(
            symbol=symbol,
            volume=volume,
            price=price,
        )

        if quantity is None:
            return None

        params = self._build_order_params(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            client_order_id=client_order_id,
        )

        if params is None:
            return None

        url = f"{self._config.fapi_url}/order"
        response = self._execute(
            method="POST",
            url=url,
            params=params,
        )

        if not response:
            return None

        return self._adapt_order_response(
            response=response,
            symbol=symbol.upper(),
        )

    def cancel_order(
        self,
        symbol: str,
        order: GatewayOrderModel,
    ) -> Optional[GatewayOrderModel]:
        """
        Cancel an existing order on Binance Futures.

        Cancels an order by its ID. Validates the symbol and order parameters before
        sending the cancellation request to Binance API.

        Args:
            symbol: Trading pair symbol (e.g., "BTCUSDT").
            order: GatewayOrderModel instance containing the order to cancel.

        Returns:
            GatewayOrderModel with updated status if cancellation was successful, None otherwise.

        Example:
            >>> component = OrderComponent(config, symbol_component)
            >>> cancelled_order = component.cancel_order(
            ...     symbol="BTCUSDT",
            ...     order=existing_order
            ... )
            >>> if cancelled_order:
            ...     print(f"Order cancelled: {cancelled_order.id}")
        """
        if not self._validate_symbol(symbol=symbol):
            return None

        if not self._validate_order(order=order):
            return None

        url = f"{self._config.fapi_url}/order"
        params = {"symbol": symbol.upper(), "orderId": order.id}
        response = self._execute(
            method="DELETE",
            url=url,
            params=params,
        )

        if not response:
            return None

        has_error, error_msg, error_code = has_api_error(response=response)

        if has_error:
            self._log.error(f"Failed to cancel order: {error_msg} (code: {error_code})")
            return None

        return self._adapt_order_response(
            response=response,
            symbol=symbol.upper(),
        )

    def modify_order(
        self,
        symbol: str,
        order: GatewayOrderModel,
    ) -> Optional[GatewayOrderModel]:
        """
        Modify an existing order on Binance Futures.

        Note: This method is not yet implemented. Binance Futures API requires
        cancelling and placing a new order to modify an existing order.

        Args:
            symbol: Trading pair symbol (e.g., "BTCUSDT").
            order: GatewayOrderModel instance containing the order to modify.

        Returns:
            GatewayOrderModel if modification was successful, None otherwise.

        Raises:
            NotImplementedError: This method is not yet implemented.
        """
        if not self._validate_symbol(symbol=symbol):
            return None

        if not self._validate_order(order=order):
            return None

        self._log.warning("modify_order is not yet implemented. Use cancel_order and place_order instead.")
        return None

    def get_orders(
        self,
        symbol: str,
        pair: str,
        order_id: int,
        start_time: datetime,
        end_time: datetime,
        limit: int = 500,
    ) -> List[GatewayOrderModel]:
        """
        Retrieve multiple orders from Binance Futures.

        Fetches orders matching the specified criteria. Supports querying by order ID
        or by time range. When querying by time range, automatically splits large date
        ranges into smaller chunks to comply with Binance API limits (7 days per request).

        Args:
            symbol: Trading pair symbol (e.g., "BTCUSDT").
            pair: Trading pair for filtering (e.g., "BTCUSDT").
            order_id: Order ID to start querying from (use 1 to query all).
            start_time: Start datetime for order query.
            end_time: End datetime for order query.
            limit: Maximum number of orders to return (default: 500, max: 1000).

        Returns:
            List of GatewayOrderModel instances matching the query criteria.

        Example:
            >>> component = OrderComponent(config, symbol_component)
            >>> orders = component.get_orders(
            ...     symbol="BTCUSDT",
            ...     pair="BTCUSDT",
            ...     order_id=1,
            ...     start_time=datetime.now() - timedelta(days=30),
            ...     end_time=datetime.now(),
            ...     limit=100
            ... )
            >>> print(f"Found {len(orders)} orders")
        """
        if not self._validate_get_orders_params(
            symbol=symbol,
            pair=pair,
            order_id=order_id,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        ):
            return []

        orders: List[GatewayOrderModel] = []
        url = f"{self._config.fapi_url}/allOrders"
        params: Dict[str, Any] = {
            "symbol": symbol.upper(),
            "pair": pair.upper(),
            "limit": min(limit, 1000),
        }

        if order_id:
            params["orderId"] = order_id

        if start_time and end_time and not order_id:
            orders = self._fetch_orders_by_time_range(
                url=url,
                params=params,
                start_time=start_time,
                end_time=end_time,
            )
        else:
            response = self._execute(
                method="GET",
                url=url,
                params=params,
            )

            if response and isinstance(response, list):
                orders.extend(self._adapt_orders_batch(response=response))

        return orders

    def get_order(
        self,
        symbol: str,
        order_id: Optional[str] = None,
        client_order_id: Optional[str] = None,
    ) -> Optional[GatewayOrderModel]:
        """
        Retrieve a single order by ID from Binance Futures.

        Fetches order details by either Binance order ID or client order ID.
        At least one of order_id or client_order_id must be provided.

        Args:
            symbol: Trading pair symbol (e.g., "BTCUSDT").
            order_id: Optional Binance order ID.
            client_order_id: Optional client order ID (custom ID provided when placing order).

        Returns:
            GatewayOrderModel if order was found, None otherwise.

        Example:
            >>> component = OrderComponent(config, symbol_component)
            >>> order = component.get_order(
            ...     symbol="BTCUSDT",
            ...     order_id="12345678"
            ... )
            >>> if order:
            ...     print(f"Order status: {order.status}")
        """
        if not self._validate_get_order_params(
            symbol=symbol,
            order_id=order_id,
            client_order_id=client_order_id,
        ):
            return None

        url = f"{self._config.fapi_url}/order"
        params = {"symbol": symbol.upper()}

        if order_id:
            params["orderId"] = order_id
        elif client_order_id:
            params["origClientOrderId"] = client_order_id

        response = self._execute(
            method="GET",
            url=url,
            params=params,
        )

        if not response:
            return None

        has_error, error_msg, error_code = has_api_error(response=response)

        if has_error:
            self._log.error(f"Failed to get order: {error_msg} (code: {error_code})")
            return None

        return self._adapt_order_response(
            response=response,
            symbol=symbol.upper(),
        )

    # ───────────────────────────────────────────────────────────
    # PRIVATE METHODS
    # ───────────────────────────────────────────────────────────
    def _validate_symbol(
        self,
        symbol: str,
    ) -> bool:
        """
        Validate that symbol parameter is a non-empty string.

        Args:
            symbol: Symbol to validate.

        Returns:
            True if symbol is valid, False otherwise.
        """
        if not symbol:
            self._log.error("symbol is required")
            return False

        if not isinstance(symbol, str):
            self._log.error("symbol must be a string")
            return False

        return True

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
            self._log.error("order is required")
            return False

        if not isinstance(order, GatewayOrderModel):
            self._log.error("order must be a GatewayOrderModel")
            return False

        if not order.id:
            self._log.error("order.id is required")
            return False

        return True

    def _validate_place_order_params(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        volume: float,
        price: Optional[float],
    ) -> bool:
        """
        Validate all parameters for place_order method.

        Args:
            symbol: Trading pair symbol.
            side: Order side enum.
            order_type: Order type enum.
            volume: Order volume.
            price: Optional order price.

        Returns:
            True if all parameters are valid, False otherwise.
        """
        if not self._validate_symbol(symbol=symbol):
            return False

        if not side:
            self._log.error("side is required")
            return False

        if not isinstance(side, OrderSide):
            self._log.error("side must be an OrderSide enum")
            return False

        if not order_type:
            self._log.error("order_type is required")
            return False

        if not isinstance(order_type, OrderType):
            self._log.error("order_type must be an OrderType enum")
            return False

        if volume is None:
            self._log.error("volume is required")
            return False

        if not isinstance(volume, (int, float)):
            self._log.error("volume must be a number")
            return False

        if volume <= 0:
            self._log.error("volume must be greater than 0")
            return False

        if order_type.requires_price() and not price:
            self._log.error("Price is required for LIMIT orders")
            return False

        if order_type.is_limit() and (price is None or price <= 0):
            self._log.error("Valid price is required for LIMIT orders")
            return False

        return True

    def _validate_get_orders_params(
        self,
        symbol: str,
        pair: str,
        order_id: int,
        start_time: datetime,
        end_time: datetime,
        limit: int,
    ) -> bool:
        """
        Validate all parameters for get_orders method.

        Args:
            symbol: Trading pair symbol.
            pair: Trading pair for filtering.
            order_id: Order ID to start from.
            start_time: Start datetime.
            end_time: End datetime.
            limit: Maximum number of orders.

        Returns:
            True if all parameters are valid, False otherwise.
        """
        if not self._validate_symbol(symbol=symbol):
            return False

        if not pair:
            self._log.error("pair is required")
            return False

        if not isinstance(pair, str):
            self._log.error("pair must be a string")
            return False

        if order_id is None:
            self._log.error("order_id is required")
            return False

        if not isinstance(order_id, int):
            self._log.error("order_id must be an integer")
            return False

        if not start_time:
            self._log.error("start_time is required")
            return False

        if not isinstance(start_time, datetime):
            self._log.error("start_time must be a datetime")
            return False

        if not end_time:
            self._log.error("end_time is required")
            return False

        if not isinstance(end_time, datetime):
            self._log.error("end_time must be a datetime")
            return False

        if start_time > end_time:
            self._log.error("start_time must be before end_time")
            return False

        if limit is not None and limit <= 0:
            self._log.error("limit must be greater than 0")
            return False

        return True

    def _validate_get_order_params(
        self,
        symbol: str,
        order_id: Optional[str],
        client_order_id: Optional[str],
    ) -> bool:
        """
        Validate all parameters for get_order method.

        Args:
            symbol: Trading pair symbol.
            order_id: Optional Binance order ID.
            client_order_id: Optional client order ID.

        Returns:
            True if all parameters are valid, False otherwise.
        """
        if not self._validate_symbol(symbol=symbol):
            return False

        if not order_id and not client_order_id:
            self._log.error("Either order_id or client_order_id must be provided")
            return False

        if order_id and not isinstance(order_id, str):
            self._log.error("order_id must be a string")
            return False

        if client_order_id and not isinstance(client_order_id, str):
            self._log.error("client_order_id must be a string")
            return False

        return True

    def _build_order_params(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: float,
        price: Optional[float],
        client_order_id: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        """
        Build order parameters dictionary for API request.

        Args:
            symbol: Trading pair symbol.
            side: Order side enum.
            order_type: Order type enum.
            quantity: Calculated order quantity.
            price: Optional order price.
            client_order_id: Optional client order ID.

        Returns:
            Dictionary of order parameters, or None if validation fails.
        """
        params: Dict[str, Any] = {
            "symbol": symbol.upper(),
            "side": side.value.upper(),
            "type": order_type.value.upper(),
            "quantity": quantity,
        }

        if order_type.is_market() and price:
            self._log.warning("Price parameter is ignored for MARKET orders")

        if order_type.is_limit():
            if price is None or price <= 0:
                return None

            params["price"] = price
            params["timeInForce"] = "GTC"

        if client_order_id:
            params["newClientOrderId"] = client_order_id

        return params

    def _fetch_orders_by_time_range(
        self,
        url: str,
        params: Dict[str, Any],
        start_time: datetime,
        end_time: datetime,
    ) -> List[GatewayOrderModel]:
        """
        Fetch orders by splitting time range into chunks.

        Binance API limits order queries to 7 days per request. This method
        automatically splits larger date ranges into smaller chunks.

        Args:
            url: API endpoint URL.
            params: Base parameters dictionary.
            start_time: Start datetime for query.
            end_time: End datetime for query.

        Returns:
            List of GatewayOrderModel instances from all time chunks.
        """
        orders: List[GatewayOrderModel] = []
        _start_time = start_time

        while _start_time < end_time:
            _end_time = min(_start_time + timedelta(days=self._MAX_ORDERS_QUERY_DAYS - 1), end_time)
            params_with_time = params.copy()
            params_with_time["startTime"] = parse_timestamp_ms(_start_time)
            params_with_time["endTime"] = parse_timestamp_ms(_end_time)

            response = self._execute(
                method="GET",
                url=url,
                params=params_with_time,
            )

            if response and isinstance(response, list):
                orders.extend(self._adapt_orders_batch(response=response))

            _start_time = _end_time + timedelta(seconds=1)

        return orders

    def _get_volume(
        self,
        symbol: str,
        volume: float,
        price: Optional[float] = None,
    ) -> Optional[float]:
        """
        Calculate and validate order volume based on symbol constraints.

        Retrieves symbol information and applies step size, precision, min/max quantity,
        and min notional constraints to ensure the volume meets Binance requirements.

        Args:
            symbol: Trading pair symbol.
            volume: Desired order volume.
            price: Optional order price for notional validation.

        Returns:
            Validated and formatted volume, or None if validation fails.
        """
        symbol_info = self._symbol_component.get_symbol_info(symbol=symbol)

        if not symbol_info:
            self._log.warning(f"Could not get symbol info for {symbol}, using volume as-is")
            return volume

        if symbol_info.step_size is None:
            self._log.warning(f"No step_size for {symbol}, using volume as-is")
            return volume

        step_size = symbol_info.step_size
        quantity_precision = symbol_info.quantity_precision

        volume_rounded_to_step = round(volume / step_size) * step_size
        volume_formatted = round(volume_rounded_to_step, quantity_precision)

        if symbol_info.min_quantity is not None and volume_formatted < symbol_info.min_quantity:
            self._log.error(f"Volume below minimum for {symbol}")
            return None

        if symbol_info.max_quantity is not None and volume_formatted > symbol_info.max_quantity:
            self._log.error(f"Volume exceeds maximum for {symbol}")
            return None

        if price and symbol_info.min_notional is not None:
            notional = price * volume_formatted

            if notional < symbol_info.min_notional:
                self._log.error(f"Notional below minimum for {symbol}")
                return None

        return volume_formatted

    def _adapt_order_response(
        self,
        response: Dict[str, Any],
        symbol: str,
    ) -> Optional[GatewayOrderModel]:
        """
        Adapt Binance API response to GatewayOrderModel.

        Transforms the raw API response into the internal order model format,
        extracting order details, status, and execution information.

        Args:
            response: Raw API response dictionary from Binance.
            symbol: Trading pair symbol.

        Returns:
            GatewayOrderModel instance with adapted data, or None if response is invalid.
        """
        if not response:
            return None

        has_error, error_msg, error_code = has_api_error(response=response)

        if has_error:
            self._log.error(f"API Error: {error_msg} (code: {error_code})")
            return None

        order_id = str(response.get("orderId", ""))
        side_str = response.get("side", "").upper()
        type_str = response.get("type", "").upper()
        status_str = response.get("status", "").upper()
        side = OrderSide.BUY if side_str == "BUY" else OrderSide.SELL

        order_type = {
            "MARKET": OrderType.MARKET,
            "LIMIT": OrderType.LIMIT,
        }.get(type_str.upper(), OrderType.MARKET)

        status = self._adapt_order_status(status_str=status_str)
        price = parse_optional_float(value=response.get("price", 0))
        executed_qty = parse_optional_float(value=response.get("executedQty", 0))
        orig_qty = parse_optional_float(value=response.get("origQty", 0))

        return GatewayOrderModel(
            id=order_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            status=status,
            volume=orig_qty or 0.0,
            executed_volume=executed_qty or 0.0,
            price=price or 0.0,
            response=response,
        )

    def _adapt_orders_batch(
        self,
        response: List[Dict[str, Any]],
    ) -> List[GatewayOrderModel]:
        """
        Adapt a batch of Binance API responses to GatewayOrderModel list.

        Processes a list of order responses and converts each to the internal
        order model format, filtering out invalid entries.

        Args:
            response: List of raw API response dictionaries from Binance.

        Returns:
            List of GatewayOrderModel instances.
        """
        orders = []

        if not response or not isinstance(response, list):
            return orders

        for order_data in response:
            if not isinstance(order_data, dict):
                continue

            adapted_order = self._adapt_order_response(
                response=order_data,
                symbol=order_data.get("symbol", "").upper(),
            )

            if adapted_order:
                orders.append(adapted_order)

        return orders

    def _adapt_order_status(
        self,
        status_str: str,
    ) -> GatewayOrderStatus:
        """
        Adapt Binance order status to GatewayOrderStatus enum.

        Maps Binance-specific order statuses to the internal gateway order status enum.

        Args:
            status_str: Binance order status string.

        Returns:
            GatewayOrderStatus enum value.
        """
        status_map = {
            BinanceOrderStatus.NEW: GatewayOrderStatus.PENDING,
            BinanceOrderStatus.PARTIALLY_FILLED: GatewayOrderStatus.PENDING,
            BinanceOrderStatus.FILLED: GatewayOrderStatus.EXECUTED,
            BinanceOrderStatus.CANCELED: GatewayOrderStatus.CANCELLED,
            BinanceOrderStatus.PENDING_CANCEL: GatewayOrderStatus.CANCELLED,
            BinanceOrderStatus.REJECTED: GatewayOrderStatus.CANCELLED,
            BinanceOrderStatus.EXPIRED: GatewayOrderStatus.CANCELLED,
        }

        try:
            binance_status = BinanceOrderStatus(status_str.upper())
            return status_map.get(binance_status, GatewayOrderStatus.PENDING)
        except ValueError:
            return GatewayOrderStatus.PENDING
