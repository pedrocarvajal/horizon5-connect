"""MetaAPI trade component for trade history retrieval."""

from datetime import UTC, datetime
from typing import Any, Dict, List, Optional

from vendor.enums.order_side import OrderSide
from vendor.helpers.parse_optional_float import parse_optional_float
from vendor.services.gateway.gateways.metaapi.components.base import BaseComponent
from vendor.services.gateway.models.gateway_trade import GatewayTradeModel


class TradeComponent(BaseComponent):
    """
    Component for handling MetaAPI trade operations.

    Provides methods to retrieve trade history (deals) from MetaAPI.
    Handles trade data retrieval, validation, and adaptation to internal
    gateway trade models.
    """

    TIMEZONE_SUFFIX_UTC = "Z"
    TIMEZONE_OFFSET_UTC = "+00:00"

    def get_trades(
        self,
        symbol: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        position_id: Optional[str] = None,
        limit: int = 1000,
    ) -> List[GatewayTradeModel]:
        """
        Retrieve trade history (deals) from MetaAPI.

        Args:
            symbol: Optional trading symbol to filter trades.
            start_time: Optional start datetime for trade history range.
            end_time: Optional end datetime for trade history range.
            position_id: Optional position ID to filter trades.
            limit: Maximum number of trades to retrieve (default: 1000).

        Returns:
            List of GatewayTradeModel instances. Empty list if request fails
            or no trades found.
        """
        if not self._config.account_id:
            self._log.error("account_id required for get_trades operation")
            return []

        if position_id:
            return self._get_trades_by_position(position_id=position_id, symbol=symbol)

        if start_time and end_time:
            return self._get_trades_by_time_range(
                start_time=start_time,
                end_time=end_time,
                symbol=symbol,
                limit=limit,
            )

        if not start_time or not end_time:
            now = datetime.now(UTC)
            if not end_time:
                end_time = now
            if not start_time:
                start_time = datetime(now.year, now.month, 1, tzinfo=UTC)

        return self._get_trades_by_time_range(
            start_time=start_time,
            end_time=end_time,
            symbol=symbol,
            limit=limit,
        )

    def _get_trades_by_position(
        self,
        position_id: str,
        symbol: Optional[str] = None,
    ) -> List[GatewayTradeModel]:
        """
        Retrieve trades by position ID.

        Args:
            position_id: Position ID to filter trades.
            symbol: Optional symbol to filter results.

        Returns:
            List of GatewayTradeModel instances.
        """
        endpoint = f"/users/current/accounts/{self._config.account_id}/history-deals/position/{position_id}"

        response = self._execute(
            method="GET",
            endpoint=endpoint,
            use_client_api=True,
        )

        if not response:
            return []

        if not isinstance(response, list):
            self._log.error(
                "Unexpected response type for deals by position",
                response_type=str(type(response)),
            )
            return []

        trades = self._adapt_trades_batch(response=response)

        if symbol:
            return [t for t in trades if t.symbol.upper() == symbol.upper()]

        return trades

    def _get_trades_by_time_range(
        self,
        start_time: datetime,
        end_time: datetime,
        symbol: Optional[str] = None,
        limit: int = 1000,
    ) -> List[GatewayTradeModel]:
        """
        Retrieve trades by time range.

        Args:
            start_time: Start datetime for trade history.
            end_time: End datetime for trade history.
            symbol: Optional symbol to filter results.
            limit: Maximum number of trades to retrieve.

        Returns:
            List of GatewayTradeModel instances.
        """
        start_iso = start_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        end_iso = end_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")

        endpoint = f"/users/current/accounts/{self._config.account_id}/history-deals/time/{start_iso}/{end_iso}"

        params: Dict[str, Any] = {
            "limit": min(limit, 1000),
        }

        response = self._execute(
            method="GET",
            endpoint=endpoint,
            params=params,
            use_client_api=True,
        )

        if not response:
            return []

        if not isinstance(response, list):
            self._log.error(
                "Unexpected response type for deals by time range",
                response_type=str(type(response)),
            )
            return []

        trades = self._adapt_trades_batch(response=response)

        if symbol:
            return [t for t in trades if t.symbol.upper() == symbol.upper()]

        return trades

    def _adapt_trade_response(
        self,
        response: Dict[str, Any],
    ) -> Optional[GatewayTradeModel]:
        """
        Adapt a single deal response from MetaAPI to GatewayTradeModel.

        Args:
            response: Dictionary containing deal data from MetaAPI.

        Returns:
            GatewayTradeModel instance or None if response is invalid.
        """
        if not response:
            return None

        trade_id = str(response.get("id", ""))
        order_id = str(response.get("orderId", ""))
        position_id = str(response.get("positionId", ""))
        symbol = response.get("symbol", "").upper()
        deal_type = response.get("type", "")
        price = parse_optional_float(value=response.get("price", 0))
        volume = parse_optional_float(value=response.get("volume", 0))
        commission = parse_optional_float(value=response.get("commission", 0))
        swap = parse_optional_float(value=response.get("swap", 0))
        time_str = response.get("time", "")

        side = self._determine_trade_side(deal_type=deal_type)
        timestamp = self._parse_iso_timestamp(time_str=time_str)

        total_commission = abs(commission or 0.0) + abs(swap or 0.0)

        return GatewayTradeModel(
            id=trade_id,
            order_id=order_id or position_id,
            symbol=symbol,
            side=side,
            price=price or 0.0,
            volume=volume or 0.0,
            commission=total_commission,
            commission_asset="",
            timestamp=timestamp,
            response=response,
        )

    def _adapt_trades_batch(
        self,
        response: List[Dict[str, Any]],
    ) -> List[GatewayTradeModel]:
        """
        Adapt a batch of deal responses from MetaAPI to GatewayTradeModel list.

        Args:
            response: List of dictionaries containing deal data.

        Returns:
            List of GatewayTradeModel instances.
        """
        trades: List[GatewayTradeModel] = []

        if not response:
            return trades

        for trade_data in response:
            adapted_trade = self._adapt_trade_response(response=trade_data)

            if adapted_trade:
                trades.append(adapted_trade)

        return trades

    def _determine_trade_side(
        self,
        deal_type: str,
    ) -> Optional[OrderSide]:
        """
        Determine the trade side based on MetaAPI deal type.

        Args:
            deal_type: MetaAPI deal type string
                (e.g., DEAL_TYPE_BUY, DEAL_TYPE_SELL).

        Returns:
            OrderSide.BUY or OrderSide.SELL, or None if unknown.
        """
        if deal_type == "DEAL_TYPE_BUY":
            return OrderSide.BUY

        if deal_type == "DEAL_TYPE_SELL":
            return OrderSide.SELL

        return None

    def _parse_iso_timestamp(
        self,
        time_str: str,
    ) -> Optional[int]:
        """
        Parse ISO 8601 timestamp string to milliseconds.

        Args:
            time_str: ISO 8601 formatted datetime string.

        Returns:
            Timestamp in milliseconds, or None if parsing fails.
        """
        if not time_str:
            return None

        try:
            normalized_time_str = time_str.replace(
                self.TIMEZONE_SUFFIX_UTC,
                self.TIMEZONE_OFFSET_UTC,
            )
            parsed_time = datetime.fromisoformat(normalized_time_str)
            return int(parsed_time.timestamp() * 1000)
        except (ValueError, AttributeError):
            return None
