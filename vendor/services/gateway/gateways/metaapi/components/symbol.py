"""MetaAPI symbol component for trading pair information."""

from typing import Any, Dict, Optional

from vendor.helpers.parse_optional_float import parse_optional_float
from vendor.services.gateway.gateways.metaapi.components.base import BaseComponent
from vendor.services.gateway.models.gateway_leverage_info import GatewayLeverageInfoModel
from vendor.services.gateway.models.gateway_symbol_info import GatewaySymbolInfoModel
from vendor.services.gateway.models.gateway_trading_fees import GatewayTradingFeesModel


class SymbolComponent(BaseComponent):
    """
    Component for handling MetaAPI symbol operations.

    Provides methods to retrieve symbol specifications, leverage info, and
    trading fees from MetaAPI. Handles data retrieval, validation, and
    adaptation to internal gateway models.
    """

    def get_symbol_info(
        self,
        symbol: str,
    ) -> Optional[GatewaySymbolInfoModel]:
        """
        Retrieve symbol specification for a given trading pair.

        Fetches symbol details including precision, min/max volume, tick size,
        and margin requirements from MetaAPI.

        Args:
            symbol: Trading pair symbol (e.g., "XAUUSD", "EURUSD").

        Returns:
            GatewaySymbolInfoModel if successful, None otherwise.
        """
        if not self._validate_symbol(symbol=symbol):
            return None

        if not self._config.account_id:
            self._log.error("account_id required for get_symbol_info operation")
            return None

        endpoint = f"/users/current/accounts/{self._config.account_id}/symbols/{symbol.upper()}/specification"

        response = self._execute(
            method="GET",
            endpoint=endpoint,
            use_client_api=True,
        )

        if not response:
            return None

        if not isinstance(response, dict):
            self._log.error(
                "Unexpected response type for symbol specification",
                response_type=str(type(response)),
            )
            return None

        return self._adapt_symbol_info(response=response)

    def get_leverage_info(
        self,
        symbol: str,
    ) -> Optional[GatewayLeverageInfoModel]:
        """
        Retrieve leverage information for a symbol.

        MetaAPI leverage is account-wide, not per-symbol. This method retrieves
        the account leverage and returns it associated with the requested symbol.

        Args:
            symbol: Trading pair symbol (e.g., "XAUUSD").

        Returns:
            GatewayLeverageInfoModel containing leverage and symbol information,
            or None if request fails.
        """
        if not self._validate_symbol(symbol=symbol):
            return None

        if not self._config.account_id:
            self._log.error("account_id required for get_leverage_info operation")
            return None

        endpoint = f"/users/current/accounts/{self._config.account_id}/account-information"

        response = self._execute(
            method="GET",
            endpoint=endpoint,
            use_client_api=True,
        )

        if not response:
            return None

        if not isinstance(response, dict):
            self._log.error(
                "Unexpected response type for account information",
                response_type=str(type(response)),
            )
            return None

        return self._adapt_leverage_info(symbol=symbol, response=response)

    def get_trading_fees(
        self,
        symbol: str,
    ) -> Optional[GatewayTradingFeesModel]:
        """
        Retrieve trading fees for a symbol.

        MetaAPI does not provide a direct endpoint for trading fees.
        This method returns default/estimated fees based on typical broker rates.

        Args:
            symbol: Trading pair symbol (e.g., "XAUUSD").

        Returns:
            GatewayTradingFeesModel with estimated fees, or None if symbol invalid.
        """
        if not self._validate_symbol(symbol=symbol):
            return None

        return GatewayTradingFeesModel(
            symbol=symbol.upper(),
            maker_commission=None,
            taker_commission=None,
            response=None,
        )

    def _adapt_symbol_info(
        self,
        response: Dict[str, Any],
    ) -> Optional[GatewaySymbolInfoModel]:
        """
        Adapt MetaAPI symbol specification to GatewaySymbolInfoModel.

        Transforms the raw API response into the internal symbol model format.

        Args:
            response: Raw API response dictionary from MetaAPI.

        Returns:
            GatewaySymbolInfoModel instance with adapted data.
        """
        if not response:
            return None

        symbol = response.get("symbol", "")
        digits = response.get("digits", 2)

        base_currency = response.get("baseCurrency", "")
        margin_currency = response.get("marginCurrency", "")

        tick_size = parse_optional_float(value=response.get("tickSize"))
        min_volume = parse_optional_float(value=response.get("minVolume"))
        max_volume = parse_optional_float(value=response.get("maxVolume"))
        volume_step = parse_optional_float(value=response.get("volumeStep"))

        initial_margin = parse_optional_float(value=response.get("initialMargin"))
        contract_size = parse_optional_float(value=response.get("contractSize"))

        margin_percent = self._calculate_margin_percent(
            initial_margin=initial_margin,
            contract_size=contract_size,
        )

        return GatewaySymbolInfoModel(
            symbol=symbol,
            base_asset=base_currency,
            quote_asset=margin_currency,
            price_precision=digits,
            quantity_precision=self._calculate_quantity_precision(volume_step=volume_step),
            min_price=None,
            max_price=None,
            tick_size=tick_size,
            min_quantity=min_volume,
            max_quantity=max_volume,
            step_size=volume_step,
            min_notional=None,
            status="TRADING",
            margin_percent=margin_percent,
            response=response,
        )

    def _adapt_leverage_info(
        self,
        symbol: str,
        response: Dict[str, Any],
    ) -> Optional[GatewayLeverageInfoModel]:
        """
        Adapt MetaAPI account information to GatewayLeverageInfoModel.

        MetaAPI provides account-wide leverage, not per-symbol.

        Args:
            symbol: Trading pair symbol.
            response: Raw API response dictionary containing account data.

        Returns:
            GatewayLeverageInfoModel with leverage information.
        """
        if not response:
            return None

        leverage = response.get("leverage", 1)

        if not isinstance(leverage, int):
            leverage = int(leverage) if leverage else 1

        return GatewayLeverageInfoModel(
            symbol=symbol.upper(),
            leverage=max(leverage, 1),
            response=response,
        )

    def _calculate_margin_percent(
        self,
        initial_margin: Optional[float],
        contract_size: Optional[float],
    ) -> Optional[float]:
        """
        Calculate margin percentage from initial margin and contract size.

        Args:
            initial_margin: Initial margin amount.
            contract_size: Contract size for the symbol.

        Returns:
            Margin percentage as decimal, or None if cannot be calculated.
        """
        if not initial_margin or not contract_size:
            return None

        if contract_size == 0:
            return None

        return initial_margin / contract_size

    def _calculate_quantity_precision(
        self,
        volume_step: Optional[float],
    ) -> int:
        """
        Calculate quantity precision from volume step.

        Args:
            volume_step: Minimum volume increment.

        Returns:
            Number of decimal places for quantity.
        """
        max_precision = 8

        if not volume_step or volume_step <= 0:
            return 2

        precision = 0
        step = volume_step

        while step < 1 and precision < max_precision:
            step *= 10
            precision += 1

        return precision

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

        return True
