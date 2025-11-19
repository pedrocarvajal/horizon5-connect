# Code reviewed on 2025-01-27 by pedrocarvajal

from datetime import datetime
from typing import Any, Dict, List, Optional

from enums.order_side import OrderSide
from helpers.parse import parse_optional_float, parse_timestamp_ms
from services.gateway.gateways.binance.components.base import BaseComponent
from services.gateway.helpers import has_api_error
from services.gateway.models.gateway_trade import GatewayTradeModel


class TradeComponent(BaseComponent):
    """
    Component for handling Binance trade operations.

    Provides methods to retrieve user trade history from Binance Futures API.
    Handles trade data retrieval, validation, and adaptation to internal models.

    Attributes:
        Inherits _config and _log from BaseComponent.
    """

    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def get_trades(
        self,
        symbol: Optional[str] = None,
        pair: Optional[str] = None,
        order_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        from_id: Optional[int] = None,
        limit: int = 500,
    ) -> List[GatewayTradeModel]:
        """
        Retrieve user trade history from Binance.

        Args:
            symbol: Optional trading symbol (e.g., "BTCUSDT") to filter trades.
            pair: Optional trading pair to filter trades.
            order_id: Optional order ID to filter trades by specific order.
            start_time: Optional start datetime for trade history range.
            end_time: Optional end datetime for trade history range.
            from_id: Optional trade ID to fetch trades from (pagination).
            limit: Maximum number of trades to retrieve (default: 500, max: 1000).

        Returns:
            List[GatewayTradeModel]: List of trade models. Returns empty list
                if validation fails, API error occurs, or no trades found.

        Example:
            >>> component = TradeComponent(config)
            >>> trades = component.get_trades(symbol="BTCUSDT", limit=100)
            >>> print(f"Found {len(trades)} trades")
        """
        if not self._validate_trades_params(
            symbol=symbol,
            pair=pair,
            order_id=order_id,
            start_time=start_time,
            end_time=end_time,
            from_id=from_id,
            limit=limit,
        ):
            return []

        params = self._build_trades_params(
            symbol=symbol,
            pair=pair,
            start_time=start_time,
            end_time=end_time,
            from_id=from_id,
            limit=limit,
        )

        url = f"{self._config.fapi_url}/userTrades"
        response = self._execute(
            method="GET",
            url=url,
            params=params if params else None,
        )

        return self._handle_trades_response(
            response=response,
            order_id=order_id,
        )

    # ───────────────────────────────────────────────────────────
    # PRIVATE METHODS
    # ───────────────────────────────────────────────────────────
    def _validate_trades_params(
        self,
        symbol: Optional[str],
        pair: Optional[str],
        order_id: Optional[str],
        start_time: Optional[datetime],
        end_time: Optional[datetime],
        from_id: Optional[int],
        limit: int,
    ) -> bool:
        """
        Validate parameters for get_trades method.

        Args:
            symbol: Trading symbol to validate.
            pair: Trading pair to validate.
            order_id: Order ID to validate.
            start_time: Start datetime to validate.
            end_time: End datetime to validate.
            from_id: Trade ID to validate.
            limit: Limit value to validate.

        Returns:
            bool: True if all validations pass, False otherwise.
        """
        if symbol and not isinstance(symbol, str):
            self._log.error("symbol must be a string")
            return False

        if pair and not isinstance(pair, str):
            self._log.error("pair must be a string")
            return False

        if order_id and not isinstance(order_id, str):
            self._log.error("order_id must be a string")
            return False

        if start_time and not isinstance(start_time, datetime):
            self._log.error("start_time must be a datetime")
            return False

        if end_time and not isinstance(end_time, datetime):
            self._log.error("end_time must be a datetime")
            return False

        if start_time and end_time and start_time > end_time:
            self._log.error("start_time must be before end_time")
            return False

        if from_id is not None and not isinstance(from_id, int):
            self._log.error("from_id must be an integer")
            return False

        if limit is not None and limit <= 0:
            self._log.error("limit must be greater than 0")
            return False

        return True

    def _build_trades_params(
        self,
        symbol: Optional[str],
        pair: Optional[str],
        start_time: Optional[datetime],
        end_time: Optional[datetime],
        from_id: Optional[int],
        limit: int,
    ) -> Dict[str, Any]:
        """
        Build request parameters for trades API call.

        Args:
            symbol: Trading symbol to include in params.
            pair: Trading pair to include in params.
            start_time: Start datetime to convert to timestamp.
            end_time: End datetime to convert to timestamp.
            from_id: Trade ID to include in params.
            limit: Limit value to include in params (capped at 1000).

        Returns:
            Dict[str, Any]: Dictionary of API request parameters.
        """
        params: Dict[str, Any] = {}

        if symbol:
            params["symbol"] = symbol.upper()

        if pair:
            params["pair"] = pair.upper()

        if start_time:
            params["startTime"] = parse_timestamp_ms(start_time)

        if end_time:
            params["endTime"] = parse_timestamp_ms(end_time)

        if from_id is not None:
            params["fromId"] = from_id

        if limit:
            params["limit"] = min(limit, 1000)

        return params

    def _handle_trades_response(
        self,
        response: Optional[Dict[str, Any]],
        order_id: Optional[str],
    ) -> List[GatewayTradeModel]:
        """
        Handle API response for trades request.

        Args:
            response: API response dictionary or None.
            order_id: Optional order ID to filter results.

        Returns:
            List[GatewayTradeModel]: List of trade models. Returns empty list
                if response is invalid or error occurs.
        """
        if not response:
            return []

        has_error, error_msg, error_code = has_api_error(response=response)

        if has_error:
            self._log.error(f"Failed to get user trades: {error_msg} (code: {error_code})")
            return []

        if not isinstance(response, list):
            self._log.error(f"Unexpected response type for userTrades: {type(response)}")
            return []

        trades = self._adapt_trades_batch(response=response)

        if order_id:
            return [trade for trade in trades if trade.order_id == str(order_id)]

        return trades

    def _adapt_trade_response(
        self,
        response: Dict[str, Any],
    ) -> Optional[GatewayTradeModel]:
        """
        Adapt a single trade response from Binance API to GatewayTradeModel.

        Args:
            response: Dictionary containing trade data from Binance API.

        Returns:
            Optional[GatewayTradeModel]: Adapted trade model or None if
                response is invalid or contains errors.
        """
        if not response:
            return None

        has_error, error_msg, error_code = has_api_error(response=response)

        if has_error:
            self._log.error(f"API Error: {error_msg} (code: {error_code})")
            return None

        trade_id = str(response.get("id", ""))
        order_id = str(response.get("orderId", ""))
        symbol = response.get("symbol", "").upper()
        side_str = response.get("side", "").upper()
        side = OrderSide.BUY if side_str == "BUY" else OrderSide.SELL
        price = parse_optional_float(value=response.get("price", 0))
        volume = parse_optional_float(value=response.get("qty", 0))
        commission = parse_optional_float(value=response.get("commission", 0))
        commission_asset = response.get("commissionAsset", "")
        timestamp = response.get("time")

        return GatewayTradeModel(
            id=trade_id,
            order_id=order_id,
            symbol=symbol,
            side=side,
            price=price or 0.0,
            volume=volume or 0.0,
            commission=commission or 0.0,
            commission_asset=commission_asset,
            timestamp=timestamp,
            response=response,
        )

    def _adapt_trades_batch(
        self,
        response: List[Dict[str, Any]],
    ) -> List[GatewayTradeModel]:
        """
        Adapt a batch of trade responses from Binance API to GatewayTradeModel list.

        Args:
            response: List of dictionaries containing trade data from Binance API.

        Returns:
            List[GatewayTradeModel]: List of adapted trade models. Returns empty
                list if response is invalid or empty.
        """
        trades: List[GatewayTradeModel] = []

        if not response or not isinstance(response, list):
            return trades

        for trade_data in response:
            if not isinstance(trade_data, dict):
                continue

            adapted_trade = self._adapt_trade_response(response=trade_data)

            if adapted_trade:
                trades.append(adapted_trade)

        return trades
