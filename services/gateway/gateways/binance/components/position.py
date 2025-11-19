# Code reviewed on 2025-11-19 by pedrocarvajal

from typing import Any, Dict, List, Optional

from enums.order_side import OrderSide
from helpers.parse import parse_optional_float
from services.gateway.gateways.binance.components.base import BaseComponent
from services.gateway.helpers import has_api_error
from services.gateway.models.gateway_position import GatewayPositionModel


class PositionComponent(BaseComponent):
    """
    Component for handling Binance position-related operations.

    Provides methods to retrieve position information and position mode settings
    from Binance Futures API. Handles position data retrieval, validation, and
    adaptation to internal position models.

    Attributes:
        _config: Binance configuration model containing API credentials and URLs.
        _log: Logging service instance for logging operations.
    """

    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────

    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def get_positions(
        self,
        symbol: Optional[str] = None,
        pair: Optional[str] = None,
    ) -> List[GatewayPositionModel]:
        """
        Retrieve positions from Binance Futures API.

        Fetches position information for all symbols or filters by symbol or pair.
        Returns a list of position models containing symbol, side, volume, entry price,
        and unrealized PnL. Returns empty list if request fails or no positions exist.

        Args:
            symbol: Optional trading pair symbol to filter positions (e.g., "BTCUSDT").
            pair: Optional trading pair to filter positions (e.g., "BTCUSDT").

        Returns:
            List of GatewayPositionModel instances. Empty list if request fails,
            validation fails, or no positions exist.

        Example:
            >>> component = PositionComponent(config)
            >>> positions = component.get_positions(symbol="BTCUSDT")
            >>> for position in positions:
            ...     print(f"{position.symbol}: {position.volume} @ {position.open_price}")
        """
        if not self._validate_symbol_or_pair(symbol=symbol, pair=pair):
            return []

        params = self._build_position_params(symbol=symbol, pair=pair)

        response = self._execute(
            method="GET",
            url=f"{self._config.fapi_v2_url}/positionRisk",
            params=params if params else None,
        )

        if not response:
            return []

        has_error, error_msg, error_code = has_api_error(response=response)

        if has_error:
            self._log.error(f"Failed to get positions: {error_msg} (code: {error_code})")
            return []

        if not isinstance(response, list):
            self._log.error(f"Unexpected response type for positionRisk: {type(response)}")
            return []

        return self._adapt_positions_batch(response=response)

    def get_position_mode(
        self,
    ) -> Optional[bool]:
        """
        Retrieve the current position mode setting from Binance.

        Returns True if dual-side position mode is enabled (hedge mode),
        False if one-way position mode is enabled, or None if the request fails.

        Returns:
            True if dual-side position mode is enabled, False if one-way mode,
            None if request fails or cannot determine mode.

        Example:
            >>> component = PositionComponent(config)
            >>> mode = component.get_position_mode()
            >>> if mode is False:
            ...     print("One-way position mode is enabled")
        """
        url = f"{self._config.fapi_url}/positionSide/dual"

        response = self._execute(
            method="GET",
            url=url,
            params=None,
        )

        if not response:
            return None

        has_error, error_msg, error_code = has_api_error(response=response)

        if has_error:
            self._log.error(f"Failed to get position mode: {error_msg} (code: {error_code})")
            return None

        dual_side_position = response.get("dualSidePosition", False)
        return bool(dual_side_position)

    # ───────────────────────────────────────────────────────────
    # PRIVATE METHODS
    # ───────────────────────────────────────────────────────────
    def _validate_symbol_or_pair(
        self,
        symbol: Optional[str],
        pair: Optional[str],
    ) -> bool:
        """
        Validate that symbol and pair parameters are strings if provided.

        Args:
            symbol: Optional symbol parameter to validate.
            pair: Optional pair parameter to validate.

        Returns:
            True if both parameters are valid (None or string), False otherwise.
        """
        if symbol and not isinstance(symbol, str):
            self._log.error("symbol must be a string")
            return False

        if pair and not isinstance(pair, str):
            self._log.error("pair must be a string")
            return False

        return True

    def _build_position_params(
        self,
        symbol: Optional[str],
        pair: Optional[str],
    ) -> Dict[str, str]:
        """
        Build query parameters dictionary for position API request.

        Args:
            symbol: Optional symbol to include in parameters (will be uppercased).
            pair: Optional pair to include in parameters (will be uppercased).

        Returns:
            Dictionary with query parameters. Empty dict if both are None.
        """
        params: Dict[str, str] = {}

        if symbol:
            params["symbol"] = symbol.upper()

        if pair:
            params["pair"] = pair.upper()

        return params

    def _determine_position_side(
        self,
        position_amt: Optional[float],
    ) -> Optional[OrderSide]:
        """
        Determine the position side based on position amount.

        Args:
            position_amt: Position amount. Positive values indicate long (BUY),
                negative values indicate short (SELL), zero or None indicates no position.

        Returns:
            OrderSide.BUY if position_amt > 0, OrderSide.SELL if position_amt < 0,
            None if position_amt is zero or None.
        """
        if position_amt and position_amt > 0:
            return OrderSide.BUY

        if position_amt and position_amt < 0:
            return OrderSide.SELL

        return None

    def _adapt_position_response(
        self,
        response: Dict[str, Any],
    ) -> Optional[GatewayPositionModel]:
        """
        Adapt a single position response from Binance API to GatewayPositionModel.

        Transforms raw API response data into the internal position model format,
        extracting symbol, position amount, entry price, unrealized PnL, and
        determining the position side.

        Args:
            response: Raw API response dictionary containing position data.

        Returns:
            GatewayPositionModel instance if response is valid, None otherwise.
        """
        if not response:
            return None

        symbol = response.get("symbol", "").upper()
        position_amt = parse_optional_float(value=response.get("positionAmt", 0))
        entry_price = parse_optional_float(value=response.get("entryPrice", 0))
        unrealized_pnl = parse_optional_float(value=response.get("unRealizedProfit", 0))
        side = self._determine_position_side(position_amt=position_amt)

        return GatewayPositionModel(
            symbol=symbol,
            side=side,
            volume=position_amt or 0.0,
            open_price=entry_price or 0.0,
            unrealized_pnl=unrealized_pnl or 0.0,
            response=response,
        )

    def _adapt_positions_batch(
        self,
        response: List[Dict[str, Any]],
    ) -> List[GatewayPositionModel]:
        """
        Adapt a batch of position responses from Binance API to GatewayPositionModel list.

        Processes a list of position data dictionaries, filtering out positions with
        zero volume and converting valid positions to GatewayPositionModel instances.

        Args:
            response: List of raw API response dictionaries containing position data.

        Returns:
            List of GatewayPositionModel instances. Empty list if response is invalid
            or contains no positions with non-zero volume.
        """
        positions = []

        if not response or not isinstance(response, list):
            return positions

        for position_data in response:
            if not isinstance(position_data, dict):
                continue

            position_amt = parse_optional_float(value=position_data.get("positionAmt", 0))

            if position_amt and position_amt != 0:
                adapted_position = self._adapt_position_response(response=position_data)

                if adapted_position:
                    positions.append(adapted_position)

        return positions
