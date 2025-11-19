# Code reviewed on 2025-11-19 by pedrocarvajal

from typing import Any, Dict, List, Optional

import requests

from enums.http_status import HttpStatus
from helpers.parse import parse_optional_float
from services.gateway.gateways.binance.components.base import BaseComponent
from services.gateway.helpers import has_api_error
from services.gateway.models.gateway_leverage_info import GatewayLeverageInfoModel
from services.gateway.models.gateway_symbol_info import GatewaySymbolInfoModel
from services.gateway.models.gateway_trading_fees import GatewayTradingFeesModel


class SymbolComponent(BaseComponent):
    """
    Component for handling Binance symbol-related operations.

    Provides methods to retrieve symbol information, trading fees, leverage info,
    and manage leverage settings for trading pairs on Binance Futures.

    Attributes:
        _config: Binance configuration model containing API credentials and URLs.
        _log: Logging service instance for logging operations.
    """

    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def get_symbol_info(
        self,
        symbol: str,
    ) -> Optional[GatewaySymbolInfoModel]:
        """
        Retrieve symbol information for a given trading pair.

        Fetches symbol details including base/quote assets, precision settings,
        price/quantity filters, and margin requirements from Binance exchange info.

        Args:
            symbol: Trading pair symbol (e.g., "BTCUSDT").

        Returns:
            GatewaySymbolInfoModel if successful, None otherwise.

        Example:
            >>> component = SymbolComponent(config)
            >>> info = component.get_symbol_info("BTCUSDT")
            >>> if info:
            ...     print(f"Base asset: {info.base_asset}")
        """
        if not self._validate_symbol(symbol=symbol):
            return None

        params = {
            "symbol": symbol.upper(),
        }

        try:
            response = requests.get(
                f"{self._config.fapi_url}/exchangeInfo",
                params=params,
            )

            if not HttpStatus.is_success_code(response.status_code):
                self._log.error(f"HTTP Error {response.status_code}: {response.text}")
                return None

            response_data = response.json()

            if not response_data:
                return None

            return self._adapt_symbol_info(
                response=response_data,
            )

        except requests.exceptions.RequestException as e:
            self._log.error(f"Error fetching symbol info: {e}")
            return None

    def get_trading_fees(
        self,
        symbol: str,
    ) -> Optional[GatewayTradingFeesModel]:
        """
        Retrieve trading fees (maker and taker commission rates) for a symbol.

        Args:
            symbol: Trading pair symbol (e.g., "BTCUSDT").

        Returns:
            GatewayTradingFeesModel containing maker and taker commission rates,
            or None if the request fails.

        Example:
            >>> component = SymbolComponent(config)
            >>> fees = component.get_trading_fees("BTCUSDT")
            >>> if fees:
            ...     print(f"Maker: {fees.maker_commission}, Taker: {fees.taker_commission}")
        """
        if not self._validate_symbol(symbol=symbol):
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
        """
        Retrieve leverage information for a symbol with an open position.

        Returns leverage details for the symbol if there is an active position.
        If no position exists, returns None.

        Args:
            symbol: Trading pair symbol (e.g., "BTCUSDT").

        Returns:
            GatewayLeverageInfoModel containing leverage and symbol information,
            or None if no position exists or request fails.

        Example:
            >>> component = SymbolComponent(config)
            >>> leverage_info = component.get_leverage_info("BTCUSDT")
            >>> if leverage_info:
            ...     print(f"Current leverage: {leverage_info.leverage}x")
        """
        if not self._validate_symbol(symbol=symbol):
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
        """
        Set leverage for a trading symbol.

        Updates the leverage multiplier for a specific trading pair.
        Leverage must be a positive integer.

        Args:
            symbol: Trading pair symbol (e.g., "BTCUSDT").
            leverage: Leverage multiplier (must be > 0).

        Returns:
            True if leverage was set successfully, False otherwise.

        Raises:
            Logs errors but does not raise exceptions.

        Example:
            >>> component = SymbolComponent(config)
            >>> success = component.set_leverage("BTCUSDT", 20)
            >>> if success:
            ...     print("Leverage set to 20x")
        """
        if not self._validate_leverage_params(symbol=symbol, leverage=leverage):
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

    def _validate_leverage_params(
        self,
        symbol: str,
        leverage: int,
    ) -> bool:
        """
        Validate symbol and leverage parameters for set_leverage method.

        Args:
            symbol: Trading pair symbol to validate.
            leverage: Leverage value to validate.

        Returns:
            True if both parameters are valid, False otherwise.
        """
        if not self._validate_symbol(symbol=symbol):
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

        return True

    def _get_trading_fees(
        self,
        symbol: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Execute API request to retrieve trading fees.

        Args:
            symbol: Trading pair symbol.

        Returns:
            API response dictionary or None if request fails.
        """
        return self._execute(
            method="GET",
            url=f"{self._config.fapi_url}/commissionRate",
            params={
                "symbol": symbol.upper(),
            },
        )

    def _adapt_symbol_info(
        self,
        response: Dict[str, Any],
    ) -> Optional[GatewaySymbolInfoModel]:
        """
        Adapt Binance API response to GatewaySymbolInfoModel.

        Parses symbol information from Binance exchange info response,
        including filters, precision settings, and margin requirements.

        Args:
            response: Raw API response dictionary from Binance.

        Returns:
            GatewaySymbolInfoModel instance or None if response is invalid.
        """
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
        """
        Parse filter information from Binance symbol filters.

        Extracts price filters, lot size filters, and min notional values
        from the filters array in Binance symbol info.

        Args:
            filters: List of filter dictionaries from Binance API.

        Returns:
            Dictionary containing parsed filter values:
            - min_price, max_price, tick_size (from PRICE_FILTER)
            - min_quantity, max_quantity, step_size (from LOT_SIZE)
            - min_notional (from MIN_NOTIONAL)
        """
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
        """
        Parse margin percentage from symbol info.

        Checks for requiredMarginPercent or maintMarginPercent fields
        in the symbol information dictionary.

        Args:
            symbol_info: Symbol information dictionary from Binance API.

        Returns:
            Margin percentage as float, or None if not found.
        """
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
        """
        Adapt Binance position risk response to GatewayLeverageInfoModel.

        Finds the first position with non-zero amount and extracts leverage info.

        Args:
            symbol: Trading pair symbol.
            response: API response list containing position data.

        Returns:
            GatewayLeverageInfoModel if position found, None otherwise.
        """
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
        """
        Adapt Binance commission rate response to GatewayTradingFeesModel.

        Handles both list and dictionary response formats from the API.

        Args:
            response: API response (can be list or dict) containing fee information.

        Returns:
            GatewayTradingFeesModel instance or None if response is invalid.
        """
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
