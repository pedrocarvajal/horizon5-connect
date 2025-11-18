from typing import Any, Dict, List, Optional

import requests

from enums.http_status import HttpStatus
from services.gateway.gateways.binance.components.base import BaseComponent
from services.gateway.helpers import has_api_error, parse_optional_float
from services.gateway.models.gateway_leverage_info import GatewayLeverageInfoModel
from services.gateway.models.gateway_symbol_info import GatewaySymbolInfoModel
from services.gateway.models.gateway_trading_fees import GatewayTradingFeesModel


class SymbolComponent(BaseComponent):
    def get_symbol_info(
        self,
        symbol: str,
    ) -> Optional[GatewaySymbolInfoModel]:
        if not symbol:
            self._log.error("symbol is required")
            return None

        if not isinstance(symbol, str):
            self._log.error("symbol must be a string")
            return None

        params = {
            "symbol": symbol.upper(),
        }

        try:
            response = requests.get(
                f"{self._config.fapi_url}/exchangeInfo",
                params=params,
            )

            if response.status_code != HttpStatus.OK.value:
                self._log.error(f"HTTP Error {response.status_code}: {response.text}")
                return None

            response = response.json()

            if not response:
                return None

            return self._adapt_symbol_info(
                response=response,
            )

        except requests.exceptions.RequestException as e:
            self._log.error(f"Error fetching symbol info: {e}")
            return None

    def get_trading_fees(
        self,
        symbol: str,
    ) -> Optional[GatewayTradingFeesModel]:
        if not symbol:
            self._log.error("symbol is required")
            return None

        if not isinstance(symbol, str):
            self._log.error("symbol must be a string")
            return None

        response = self._get_trading_fees(
            symbol=symbol,
        )

        if not response:
            return None

        return self._adapt_trading_fees(response=response)

    def get_leverage_info(
        self,
        symbol: str,
    ) -> Optional[GatewayLeverageInfoModel]:
        if not symbol:
            self._log.error("symbol is required")
            return None

        if not isinstance(symbol, str):
            self._log.error("symbol must be a string")
            return None

        url = f"{self._config.fapi_v2_url}/positionRisk"
        params = {"symbol": symbol.upper()}

        response = self._execute(
            method="GET",
            url=url,
            params=params,
        )

        if not response:
            return None

        has_error, error_msg, error_code = has_api_error(response=response)

        if has_error:
            self._log.error(f"Failed to get leverage info: {error_msg} (code: {error_code})")
            return None

        return self._adapt_leverage_info(
            symbol=symbol,
            response=response,
        )

    def set_leverage(
        self,
        symbol: str,
        leverage: int,
    ) -> bool:
        if not symbol:
            self._log.error("symbol is required")
            return False

        if not isinstance(symbol, str):
            self._log.error("symbol must be a string")
            return False

        if leverage is None:
            self._log.error("leverage is required")
            return False

        if not isinstance(leverage, int):
            self._log.error("leverage must be an integer")
            return False

        if leverage <= 0:
            self._log.error("leverage must be greater than 0")
            return False

        url = f"{self._config.fapi_url}/leverage"
        params = {
            "symbol": symbol.upper(),
            "leverage": leverage,
        }

        result = self._execute(
            method="POST",
            url=url,
            params=params,
        )

        if not result:
            return False

        has_error, error_msg, error_code = has_api_error(response=result)

        if has_error:
            self._log.error(f"Failed to set leverage: {error_msg} (code: {error_code})")
            return False

        return True

    def _get_trading_fees(
        self,
        symbol: str,
    ) -> Optional[Dict[str, Any]]:
        return self._execute(
            method="GET",
            url=f"{self._config.fapi_url}/commissionRate",
            params={
                "symbol": symbol.upper(),
            },
        )

    # ───────────────────────────────────────────────────────────
    # PRIVATE METHODS
    # ───────────────────────────────────────────────────────────
    def _adapt_symbol_info(
        self,
        response: Dict[str, Any],
    ) -> Optional[GatewaySymbolInfoModel]:
        if not response or "symbols" not in response or len(response["symbols"]) == 0:
            return None

        symbol_info = response["symbols"][0]
        filters = self._parse_filters(filters=symbol_info.get("filters", []))
        margin_percent = self._parse_margin_percent(symbol_info=symbol_info)

        return GatewaySymbolInfoModel(
            symbol=symbol_info.get("symbol", ""),
            base_asset=symbol_info.get("baseAsset", ""),
            quote_asset=symbol_info.get("quoteAsset", ""),
            price_precision=symbol_info.get("pricePrecision", 2),
            quantity_precision=symbol_info.get("quantityPrecision", 2),
            min_price=filters.get("min_price"),
            max_price=filters.get("max_price"),
            tick_size=filters.get("tick_size"),
            min_quantity=filters.get("min_quantity"),
            max_quantity=filters.get("max_quantity"),
            step_size=filters.get("step_size"),
            min_notional=filters.get("min_notional"),
            status=symbol_info.get("status", "TRADING"),
            margin_percent=margin_percent,
            response=symbol_info,
        )

    def _parse_filters(
        self,
        filters: List[Dict[str, Any]],
    ) -> Dict[str, Optional[float]]:
        result = {
            "min_price": None,
            "max_price": None,
            "tick_size": None,
            "min_quantity": None,
            "max_quantity": None,
            "step_size": None,
            "min_notional": None,
        }

        for filter_item in filters:
            filter_type = filter_item.get("filterType", "")

            if filter_type == "PRICE_FILTER":
                result["min_price"] = parse_optional_float(
                    value=filter_item.get("minPrice"),
                )

                result["max_price"] = parse_optional_float(
                    value=filter_item.get("maxPrice"),
                )

                result["tick_size"] = parse_optional_float(
                    value=filter_item.get("tickSize"),
                )

            elif filter_type == "LOT_SIZE":
                result["min_quantity"] = parse_optional_float(
                    value=filter_item.get("minQty"),
                )

                result["max_quantity"] = parse_optional_float(
                    value=filter_item.get("maxQty"),
                )

                result["step_size"] = parse_optional_float(
                    value=filter_item.get("stepSize"),
                )

            elif filter_type == "MIN_NOTIONAL":
                result["min_notional"] = parse_optional_float(
                    value=filter_item.get("notional"),
                )

        return result

    def _parse_margin_percent(
        self,
        symbol_info: Dict[str, Any],
    ) -> Optional[float]:
        if "requiredMarginPercent" in symbol_info:
            return parse_optional_float(
                value=symbol_info.get("requiredMarginPercent"),
            )

        if "maintMarginPercent" in symbol_info:
            return parse_optional_float(
                value=symbol_info.get("maintMarginPercent"),
            )

        return None

    def _adapt_leverage_info(
        self,
        symbol: str,
        response: Any,
    ) -> Optional[GatewayLeverageInfoModel]:
        if not response:
            return None

        if not isinstance(response, list) or len(response) == 0:
            return None

        for position_data in response:
            if not isinstance(position_data, dict):
                continue

            position_amt = parse_optional_float(value=position_data.get("positionAmt", 0))

            if position_amt and position_amt != 0:
                leverage = int(position_data.get("leverage", 1))

                return GatewayLeverageInfoModel(
                    symbol=symbol.upper(),
                    leverage=leverage,
                    response=position_data,
                )

        return None

    def _adapt_trading_fees(
        self,
        response: Dict[str, Any],
    ) -> Optional[GatewayTradingFeesModel]:
        if not response:
            return None

        fees_data = response[0] if isinstance(response, list) and len(response) > 0 else response

        if not fees_data:
            return None

        symbol_name = fees_data.get("symbol", "")
        maker_commission = fees_data.get("makerCommissionRate")
        taker_commission = fees_data.get("takerCommissionRate")

        return GatewayTradingFeesModel(
            symbol=symbol_name,
            maker_commission=maker_commission,
            taker_commission=taker_commission,
            response=fees_data,
        )
