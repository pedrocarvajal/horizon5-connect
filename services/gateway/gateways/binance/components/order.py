from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from enums.order_side import OrderSide
from enums.order_type import OrderType
from services.gateway.gateways.binance.components.base import BaseComponent
from services.gateway.gateways.binance.components.symbol import SymbolComponent
from services.gateway.gateways.binance.enums.binance_order_status import BinanceOrderStatus
from helpers.parse import parse_optional_float, parse_timestamp_ms
from services.gateway.helpers import has_api_error
from services.gateway.models.enums.gateway_order_status import GatewayOrderStatus
from services.gateway.models.gateway_order import GatewayOrderModel


class OrderComponent(BaseComponent):
    _MAX_ORDERS_QUERY_DAYS = 7
    _symbol_component: SymbolComponent

    def __init__(
        self,
        config: Any,
    ) -> None:
        super().__init__(config)

        self._symbol_component = SymbolComponent(
            config=config,
        )

    def place_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        volume: float,
        price: Optional[float] = None,
        client_order_id: Optional[str] = None,
    ) -> Optional[GatewayOrderModel]:
        if not symbol:
            self._log.error("symbol is required")
            return None

        if not isinstance(symbol, str):
            self._log.error("symbol must be a string")
            return None

        if not side:
            self._log.error("side is required")
            return None

        if not isinstance(side, OrderSide):
            self._log.error("side must be an OrderSide enum")
            return None

        if not order_type:
            self._log.error("order_type is required")
            return None

        if not isinstance(order_type, OrderType):
            self._log.error("order_type must be an OrderType enum")
            return None

        if volume is None:
            self._log.error("volume is required")
            return None

        if not isinstance(volume, (int, float)):
            self._log.error("volume must be a number")
            return None

        if volume <= 0:
            self._log.error("volume must be greater than 0")
            return None

        quantity = self._get_volume(
            symbol=symbol,
            volume=volume,
            price=price,
        )

        if quantity is None:
            return None

        url = f"{self._config.fapi_url}/order"
        params = {
            "symbol": symbol,
            "side": side.value.upper(),
            "type": order_type.value.upper(),
            "quantity": quantity,
        }

        if order_type.requires_price() and not price:
            self._log.error("Price is required for LIMIT orders")
            return None

        if order_type.is_market() and price:
            self._log.warning("Price parameter is ignored for MARKET orders")

        if order_type.is_limit():
            if price is None or price <= 0:
                self._log.error("Valid price is required for LIMIT orders")
                return None

            params["price"] = price
            params["timeInForce"] = "GTC"

        if client_order_id:
            params["newClientOrderId"] = client_order_id

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
        if not symbol:
            self._log.error("symbol is required")
            return None

        if not isinstance(symbol, str):
            self._log.error("symbol must be a string")
            return None

        if not order:
            self._log.error("order is required")
            return None

        if not isinstance(order, GatewayOrderModel):
            self._log.error("order must be a GatewayOrderModel")
            return None

        if not order.id:
            self._log.error("order.id is required")
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
        if not symbol:
            self._log.error("symbol is required")
            return None

        if not isinstance(symbol, str):
            self._log.error("symbol must be a string")
            return None

        if not order:
            self._log.error("order is required")
            return None

        if not isinstance(order, GatewayOrderModel):
            self._log.error("order must be a GatewayOrderModel")
            return None

        pass

    def get_orders(
        self,
        symbol: str,
        pair: str,
        order_id: int,
        start_time: datetime,
        end_time: datetime,
        limit: int = 500,
    ) -> List[GatewayOrderModel]:
        if not symbol:
            self._log.error("symbol is required")
            return []

        if not isinstance(symbol, str):
            self._log.error("symbol must be a string")
            return []

        if not pair:
            self._log.error("pair is required")
            return []

        if not isinstance(pair, str):
            self._log.error("pair must be a string")
            return []

        if order_id is None:
            self._log.error("order_id is required")
            return []

        if not isinstance(order_id, int):
            self._log.error("order_id must be an integer")
            return []

        if not start_time:
            self._log.error("start_time is required")
            return []

        if not isinstance(start_time, datetime):
            self._log.error("start_time must be a datetime")
            return []

        if not end_time:
            self._log.error("end_time is required")
            return []

        if not isinstance(end_time, datetime):
            self._log.error("end_time must be a datetime")
            return []

        if start_time > end_time:
            self._log.error("start_time must be before end_time")
            return []

        if limit is not None and limit <= 0:
            self._log.error("limit must be greater than 0")
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
        if not symbol:
            self._log.error("symbol is required")
            return None

        if not isinstance(symbol, str):
            self._log.error("symbol must be a string")
            return None

        if not order_id and not client_order_id:
            self._log.error("Either order_id or client_order_id must be provided")
            return None

        if order_id and not isinstance(order_id, str):
            self._log.error("order_id must be a string")
            return None

        if client_order_id and not isinstance(client_order_id, str):
            self._log.error("client_order_id must be a string")
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
    def _get_volume(
        self,
        symbol: str,
        volume: float,
        price: Optional[float] = None,
    ) -> Optional[float]:
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
            "STOP": OrderType.STOP_LOSS,
            "STOP_MARKET": OrderType.STOP_LOSS,
            "TAKE_PROFIT": OrderType.TAKE_PROFIT,
            "TAKE_PROFIT_MARKET": OrderType.TAKE_PROFIT,
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
        status_map = {
            BinanceOrderStatus.NEW.value: GatewayOrderStatus.PENDING,
            BinanceOrderStatus.PARTIALLY_FILLED.value: GatewayOrderStatus.PENDING,
            BinanceOrderStatus.FILLED.value: GatewayOrderStatus.EXECUTED,
            BinanceOrderStatus.CANCELED.value: GatewayOrderStatus.CANCELLED,
            BinanceOrderStatus.PENDING_CANCEL.value: GatewayOrderStatus.CANCELLED,
            BinanceOrderStatus.REJECTED.value: GatewayOrderStatus.CANCELLED,
            BinanceOrderStatus.EXPIRED.value: GatewayOrderStatus.CANCELLED,
        }

        return status_map.get(status_str.upper(), GatewayOrderStatus.PENDING)
