from typing import Any, Dict, List, Optional

from enums.order_side import OrderSide
from services.gateway.gateways.binance.components.base import BaseComponent
from services.gateway.helpers import has_api_error, parse_optional_float
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

        url = f"{self._config.fapi_url}/positionRisk"

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
        mark_price = parse_optional_float(value=response.get("markPrice", 0))
        liquidation_price = parse_optional_float(value=response.get("liquidationPrice", 0))
        leverage = int(response.get("leverage", 1))
        margin = parse_optional_float(value=response.get("isolatedMargin", 0))
        unrealized_pnl = parse_optional_float(value=response.get("unRealizedProfit", 0))
        percentage = parse_optional_float(value=response.get("percentage", 0))
        side = None

        if position_amt and position_amt > 0:
            side = OrderSide.BUY

        elif position_amt and position_amt < 0:
            side = OrderSide.SELL

        return GatewayPositionModel(
            symbol=symbol,
            side=side,
            quantity=position_amt or 0.0,
            entry_price=entry_price or 0.0,
            mark_price=mark_price or 0.0,
            liquidation_price=liquidation_price or 0.0,
            leverage=leverage,
            margin=margin or 0.0,
            unrealized_pnl=unrealized_pnl or 0.0,
            percentage=percentage or 0.0,
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
