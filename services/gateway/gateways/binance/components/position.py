from typing import Any, Dict, List, Optional

from enums.order_side import OrderSide
from services.gateway.gateways.binance.components.base import BaseComponent
from helpers.parse import parse_optional_float
from services.gateway.helpers import has_api_error
from services.gateway.models.gateway_position import GatewayPositionModel


class PositionComponent(BaseComponent):
    def get_positions(
        self,
        symbol: Optional[str] = None,
        pair: Optional[str] = None,
    ) -> List[GatewayPositionModel]:
        if symbol and not isinstance(symbol, str):
            self._log.error("symbol must be a string")
            return []

        if pair and not isinstance(pair, str):
            self._log.error("pair must be a string")
            return []

        url = f"{self._config.fapi_v2_url}/positionRisk"

        params = {}

        if symbol:
            params["symbol"] = symbol.upper()

        if pair:
            params["pair"] = pair.upper()

        response = self._execute(
            method="GET",
            url=url,
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
    def _adapt_position_response(
        self,
        response: Dict[str, Any],
    ) -> Optional[GatewayPositionModel]:
        if not response:
            return None

        symbol = response.get("symbol", "").upper()
        position_amt = parse_optional_float(value=response.get("positionAmt", 0))
        entry_price = parse_optional_float(value=response.get("entryPrice", 0))
        unrealized_pnl = parse_optional_float(value=response.get("unRealizedProfit", 0))
        side = None

        if position_amt and position_amt > 0:
            side = OrderSide.BUY

        elif position_amt and position_amt < 0:
            side = OrderSide.SELL

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
