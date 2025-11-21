# Code reviewed on 2025-11-19 by pedrocarvajal

from typing import Any, Dict, List, Optional

from helpers.parse import parse_optional_float
from services.gateway.gateways.binance.components.base import BaseComponent
from services.gateway.gateways.binance.components.position import PositionComponent
from services.gateway.gateways.binance.components.symbol import SymbolComponent
from services.gateway.gateways.binance.models.config import BinanceConfigModel
from services.gateway.helpers import has_api_error
from services.gateway.models.gateway_account import (
    GatewayAccountBalanceModel,
    GatewayAccountModel,
)


class AccountComponent(BaseComponent):
    """
    Component for handling Binance account-related operations.

    Provides methods to retrieve account information, balances, and verification
    checks for trading configuration. Handles account data retrieval, validation,
    and adaptation to internal models.

    Attributes:
        _position_component: Component for position-related operations.
        _symbol_component: Component for symbol-related operations.
    """

    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    _position_component: PositionComponent
    _symbol_component: SymbolComponent

    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(
        self,
        config: BinanceConfigModel,
    ) -> None:
        """
        Initialize the account component.

        Args:
            config: Binance configuration model containing API credentials and URLs.
        """
        super().__init__(config)

        self._position_component = PositionComponent(
            config=config,
        )

        self._symbol_component = SymbolComponent(
            config=config,
        )

    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def get_account(
        self,
        **kwargs: Any,  # noqa: ARG002
    ) -> Optional[GatewayAccountModel]:
        """
        Retrieve account information from Binance.

        Fetches account details including balances, margin, exposure, and PnL
        from Binance Futures API. Returns None if the request fails or API
        returns an error.

        Args:
            **kwargs: Additional keyword arguments (currently unused).

        Returns:
            GatewayAccountModel if successful, None otherwise.

        Example:
            >>> component = AccountComponent(config)
            >>> account = component.get_account()
            >>> if account:
            ...     print(f"Balance: {account.balance}")
        """
        url = f"{self._config.fapi_v2_url}/account"

        response = self._execute(
            method="GET",
            url=url,
            params=None,
        )

        if not response:
            return None

        has_error, error_msg, error_code = has_api_error(response=response)

        if has_error:
            self._log.error(f"Failed to get account info: {error_msg} (code: {error_code})")
            return None

        return self._adapt_account_response(
            response=response,
        )

    def get_verification(
        self,
        symbol: str = "BTCUSDT",
    ) -> Dict[str, bool]:
        """
        Verify account configuration for trading.

        Performs multiple checks to ensure the account is properly configured
        for trading, including credentials, leverage settings, balance, margin mode,
        position mode, and trading permissions.

        Args:
            symbol: Trading pair symbol to check leverage for (default: "BTCUSDT").

        Returns:
            Dictionary containing verification results with keys:
                - credentials_configured: Whether API key and secret are set
                - required_leverage: Whether leverage is >= 1
                - usdt_balance: Whether USDT balance > 0
                - cross_margin: Whether account is in cross margin mode
                - one_way_mode: Whether account is in one-way position mode
                - trading_permissions: Whether trading is enabled

        Example:
            >>> component = AccountComponent(config)
            >>> verification = component.get_verification(symbol="BTCUSDT")
            >>> if verification["credentials_configured"]:
            ...     print("Credentials are configured correctly")
        """
        if not self._check_credentials():
            return {
                "credentials_configured": False,
                "required_leverage": False,
                "usdt_balance": False,
                "cross_margin": False,
                "one_way_mode": False,
                "trading_permissions": False,
            }

        return {
            "credentials_configured": True,
            "required_leverage": self._check_leverage(symbol=symbol),
            "usdt_balance": self._check_usdt_balance(),
            "cross_margin": self._check_cross_margin(),
            "one_way_mode": self._check_one_way_mode(),
            "trading_permissions": self._check_trading_permissions(),
        }

    # ───────────────────────────────────────────────────────────
    # PRIVATE METHODS
    # ───────────────────────────────────────────────────────────
    def _adapt_account_response(
        self,
        response: Dict[str, Any],
    ) -> Optional[GatewayAccountModel]:
        """
        Adapt Binance API response to GatewayAccountModel.

        Transforms the raw API response into the internal account model format,
        extracting balances, totals, and account metrics.

        Args:
            response: Raw API response dictionary from Binance.

        Returns:
            GatewayAccountModel instance with adapted data.
        """
        balances = self._build_balances(response=response)

        total_wallet_balance = parse_optional_float(value=response.get("totalWalletBalance", 0)) or 0.0
        total_margin_balance = parse_optional_float(value=response.get("totalMarginBalance", 0)) or 0.0
        total_unrealized_pnl = parse_optional_float(value=response.get("totalUnrealizedProfit", 0)) or 0.0
        total_position_initial_margin = (
            parse_optional_float(value=response.get("totalPositionInitialMargin", 0)) or 0.0
        )
        total_open_order_initial_margin = (
            parse_optional_float(value=response.get("totalOpenOrderInitialMargin", 0)) or 0.0
        )

        return GatewayAccountModel(
            balances=balances,
            balance=total_wallet_balance,
            nav=total_margin_balance,
            locked=total_open_order_initial_margin,
            margin=total_position_initial_margin,
            exposure=total_position_initial_margin,
            pnl=total_unrealized_pnl,
            response=response,
        )

    def _build_balances(
        self,
        response: Dict[str, Any],
    ) -> List[GatewayAccountBalanceModel]:
        """
        Build list of balance models from API response.

        Extracts asset balances from the API response and creates
        GatewayAccountBalanceModel instances for each asset.

        Args:
            response: Raw API response dictionary containing assets data.

        Returns:
            List of GatewayAccountBalanceModel instances.
        """
        balances: List[GatewayAccountBalanceModel] = []
        assets = response.get("assets", [])

        for asset_data in assets:
            wallet_balance = parse_optional_float(value=asset_data.get("walletBalance", 0)) or 0.0
            locked_balance = parse_optional_float(value=asset_data.get("locked", 0)) or 0.0

            balances.append(
                GatewayAccountBalanceModel(
                    asset=asset_data.get("asset", ""),
                    balance=wallet_balance,
                    locked=locked_balance,
                    response=asset_data,
                )
            )

        return balances

    def _check_credentials(
        self,
    ) -> bool:
        """
        Check if API credentials are configured.

        Verifies that both API key and secret are set in the configuration.

        Returns:
            True if both credentials are configured, False otherwise.
        """
        return bool(self._config.api_key and self._config.api_secret)

    def _check_leverage(
        self,
        symbol: str,
    ) -> bool:
        """
        Check if leverage is configured correctly for the symbol.

        Verifies that the leverage setting for the given symbol is >= 1.

        Args:
            symbol: Trading pair symbol to check.

        Returns:
            True if leverage >= 1, False otherwise.
        """
        leverage_info = self._symbol_component.get_leverage_info(
            symbol=symbol,
        )

        if leverage_info:
            return leverage_info.leverage >= 1

        return False

    def _check_usdt_balance(
        self,
    ) -> bool:
        """
        Check if account has USDT balance > 0.

        Returns:
            True if USDT balance exists and is > 0, False otherwise.
        """
        account = self.get_account()

        if account:
            for balance in account.balances:
                if balance.asset == "USDT":
                    return balance.balance > 0

        return False

    def _check_cross_margin(
        self,
    ) -> bool:
        """
        Check if account is configured for cross margin mode.

        Verifies that all positions use cross margin mode. Returns True
        if no positions exist (default state).

        Returns:
            True if all positions use cross margin or no positions exist,
            False otherwise.
        """
        positions = self._position_component.get_positions()

        if positions:
            margin_types = set()

            for position in positions:
                margin_type = position.response.get("marginType", "")

                if margin_type:
                    margin_types.add(margin_type.lower())

            return "cross" in margin_types and len(margin_types) == 1
        return True

    def _check_one_way_mode(
        self,
    ) -> bool:
        """
        Check if account is in one-way position mode.

        One-way mode means dualSidePosition is False. Returns False
        if position mode cannot be determined.

        Returns:
            True if in one-way mode, False otherwise.
        """
        position_mode = self._position_component.get_position_mode()
        if position_mode is not None:
            return not position_mode
        return False

    def _check_trading_permissions(
        self,
    ) -> bool:
        """
        Check if trading is enabled for the account.

        Returns:
            True if trading is enabled (canTrade is True), False otherwise.
        """
        account = self.get_account()

        if account and account.response:
            return account.response.get("canTrade", False)

        return False
