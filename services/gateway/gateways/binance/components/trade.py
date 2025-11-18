from datetime import datetime
from typing import Any, Dict, List, Optional

from enums.order_side import OrderSide
from services.gateway.gateways.binance.components.base import BaseComponent
from services.gateway.helpers import has_api_error, parse_optional_float, parse_timestamp_ms
from services.gateway.models.gateway_trade import GatewayTradeModel


class TradeComponent(BaseComponent):
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
        if symbol and not isinstance(symbol, str):
            self._log.error("symbol must be a string")
            return []

        if pair and not isinstance(pair, str):
            self._log.error("pair must be a string")
            return []

        if order_id and not isinstance(order_id, str):
            self._log.error("order_id must be a string")
            return []

        if start_time and not isinstance(start_time, datetime):
            self._log.error("start_time must be a datetime")
            return []

        if end_time and not isinstance(end_time, datetime):
            self._log.error("end_time must be a datetime")
            return []

        if start_time and end_time and start_time > end_time:
            self._log.error("start_time must be before end_time")
            return []

        if from_id is not None and not isinstance(from_id, int):
            self._log.error("from_id must be an integer")
            return []

        if limit is not None and limit <= 0:
            self._log.error("limit must be greater than 0")
            return []

        start_timestamp_ms = parse_timestamp_ms(start_time) if start_time else None
        end_timestamp_ms = parse_timestamp_ms(end_time) if end_time else None

        url = f"{self._config.fapi_url}/userTrades"

        params = {}

        if symbol:
            params["symbol"] = symbol.upper()

        if pair:
            params["pair"] = pair.upper()

        if start_timestamp_ms:
            params["startTime"] = start_timestamp_ms

        if end_timestamp_ms:
            params["endTime"] = end_timestamp_ms

        if from_id is not None:
            params["fromId"] = from_id

        if limit:
            params["limit"] = min(limit, 1000)

        response = self._execute(
            method="GET",
            url=url,
            params=params if params else None,
        )

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
            trades = [trade for trade in trades if trade.order_id == str(order_id)]

        return trades

    # ───────────────────────────────────────────────────────────
    # PRIVATE METHODS
    # ───────────────────────────────────────────────────────────
    def _adapt_trade_response(
        self,
        response: Dict[str, Any],
    ) -> Optional[GatewayTradeModel]:
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
        trades = []

        if not response or not isinstance(response, list):
            return trades

        for trade_data in response:
            if not isinstance(trade_data, dict):
                continue

            adapted_trade = self._adapt_trade_response(response=trade_data)

            if adapted_trade:
                trades.append(adapted_trade)

        return trades
