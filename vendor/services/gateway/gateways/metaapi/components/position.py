"""MetaAPI position component for position data retrieval."""

from typing import Any, Dict, List, Optional

from vendor.enums.order_side import OrderSide
from vendor.helpers.parse_optional_float import parse_optional_float
from vendor.services.gateway.gateways.metaapi.components.base import BaseComponent
from vendor.services.gateway.models.gateway_position import GatewayPositionModel


class PositionComponent(BaseComponent):
    """Component for handling MetaAPI position-related operations.

    Provides methods to retrieve position information from MetaAPI.
    Handles position data retrieval, validation, and adaptation to
    internal position models matching the Binance gateway response format.
    """

    def get_position(
        self,
        position_id: str,
    ) -> Optional[GatewayPositionModel]:
        """
        Retrieve a single position by ID from MetaAPI.

        Args:
            position_id: Position ID/ticket to retrieve.

        Returns:
            GatewayPositionModel if position was found, None otherwise.
        """
        if not self._config.account_id:
            self._log.error("account_id required for get_position")
            return None

        if not position_id:
            self._log.error("position_id is required")
            return None

        endpoint = f"/users/current/accounts/{self._config.account_id}/positions/{position_id}"

        response = self._execute(
            method="GET",
            endpoint=endpoint,
            use_client_api=True,
        )

        if not response:
            return None

        if not isinstance(response, dict):
            self._log.error(f"Unexpected response type for position: {type(response)}")
            return None

        return self._adapt_position_response(response=response)

    def get_positions(
        self,
        symbol: Optional[str] = None,
    ) -> List[GatewayPositionModel]:
        """
        Retrieve positions from MetaAPI.

        Fetches position information for all symbols or filters by symbol.
        Returns a list of position models containing symbol, side, volume,
        entry price, and unrealized PnL.

        Args:
            symbol: Optional trading symbol to filter positions (e.g., "XAUUSD").

        Returns:
            List of GatewayPositionModel instances. Empty list if request fails
            or no positions exist.
        """
        if not self._config.account_id:
            self._log.error("account_id required for get_positions")
            return []

        endpoint = f"/users/current/accounts/{self._config.account_id}/positions"

        response = self._execute(
            method="GET",
            endpoint=endpoint,
            use_client_api=True,
        )

        if not response:
            return []

        if not isinstance(response, list):
            self._log.error(f"Unexpected response type for positions: {type(response)}")
            return []

        positions = self._adapt_positions_batch(response=response)

        if symbol:
            return [p for p in positions if p.symbol.upper() == symbol.upper()]

        return positions

    def _adapt_position_response(
        self,
        response: Dict[str, Any],
    ) -> Optional[GatewayPositionModel]:
        """
        Adapt a single position response from MetaAPI to GatewayPositionModel.

        Transforms raw API response data into the internal position model format,
        matching the Binance gateway response structure.

        Args:
            response: Raw API response dictionary containing position data.

        Returns:
            GatewayPositionModel instance if response is valid, None otherwise.
        """
        if not response:
            return None

        symbol = response.get("symbol", "").upper()
        position_type = response.get("type", "")
        volume = parse_optional_float(value=response.get("volume", 0))
        open_price = parse_optional_float(value=response.get("openPrice", 0))
        unrealized_profit = parse_optional_float(value=response.get("unrealizedProfit", 0))

        side = self._determine_position_side(position_type=position_type)

        adjusted_volume = volume or 0.0
        if side == OrderSide.SELL and adjusted_volume > 0:
            adjusted_volume = -adjusted_volume

        return GatewayPositionModel(
            symbol=symbol,
            side=side,
            volume=adjusted_volume,
            open_price=open_price or 0.0,
            unrealized_pnl=unrealized_profit or 0.0,
            response=response,
        )

    def _adapt_positions_batch(
        self,
        response: List[Dict[str, Any]],
    ) -> List[GatewayPositionModel]:
        """
        Adapt a batch of position responses from MetaAPI to GatewayPositionModel list.

        Args:
            response: List of raw API response dictionaries containing position data.

        Returns:
            List of GatewayPositionModel instances.
        """
        positions: List[GatewayPositionModel] = []

        if not response:
            return positions

        for position_data in response:
            adapted_position = self._adapt_position_response(response=position_data)

            if adapted_position and adapted_position.volume != 0:
                positions.append(adapted_position)

        return positions

    def _determine_position_side(
        self,
        position_type: str,
    ) -> Optional[OrderSide]:
        """
        Determine the position side based on MetaAPI position type.

        Args:
            position_type: MetaAPI position type string
                (POSITION_TYPE_BUY or POSITION_TYPE_SELL).

        Returns:
            OrderSide.BUY for long positions, OrderSide.SELL for short positions,
            None if type is unknown.
        """
        if position_type == "POSITION_TYPE_BUY":
            return OrderSide.BUY

        if position_type == "POSITION_TYPE_SELL":
            return OrderSide.SELL

        return None
