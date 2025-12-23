"""MetaAPI account component for account information retrieval."""

from typing import Any, Dict, List, Optional

from vendor.helpers.parse_optional_float import parse_optional_float
from vendor.services.gateway.gateways.metaapi.components.base import BaseComponent
from vendor.services.gateway.models.gateway_account import (
    GatewayAccountBalanceModel,
    GatewayAccountModel,
)


class AccountComponent(BaseComponent):
    """
    Component for handling MetaAPI account operations.

    Provides methods to retrieve account information from MetaAPI.
    Handles account data retrieval, validation, and adaptation to internal
    gateway models.
    """

    def get_account(self) -> Optional[GatewayAccountModel]:
        """
        Retrieve account information from MetaAPI.

        Fetches account details including balance, equity, margin, and free margin
        from MetaAPI. Returns None if the request fails.

        Returns:
            GatewayAccountModel if successful, None otherwise.
        """
        if not self._config.account_id:
            self._log.error("account_id required for get_account operation")
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

        return self._adapt_account_response(response=response)

    def get_verification(self) -> Dict[str, bool]:
        """
        Verify account configuration for trading.

        Performs checks to ensure the account is properly configured
        for trading, including credentials and trading permissions.

        Returns:
            Dictionary containing verification results with keys:
                - credentials_configured: Whether auth_token and account_id are set
                - required_leverage: Always True for MetaTrader (leverage is broker-managed)
                - usdt_balance: Whether account has positive balance
                - cross_margin: Always True for MetaTrader (not applicable)
                - one_way_mode: Always True for MetaTrader (not applicable)
                - trading_permissions: Whether trading is enabled on the account
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

        account = self.get_account()

        if not account:
            return {
                "credentials_configured": True,
                "required_leverage": False,
                "usdt_balance": False,
                "cross_margin": False,
                "one_way_mode": False,
                "trading_permissions": False,
            }

        trading_allowed = self._check_trading_allowed(response=account.response)
        has_balance = account.balance > 0

        return {
            "credentials_configured": True,
            "required_leverage": True,
            "usdt_balance": has_balance,
            "cross_margin": True,
            "one_way_mode": True,
            "trading_permissions": trading_allowed,
        }

    def _adapt_account_response(
        self,
        response: Dict[str, Any],
    ) -> Optional[GatewayAccountModel]:
        """
        Adapt MetaAPI account response to GatewayAccountModel.

        Transforms the raw API response into the internal account model format.

        Args:
            response: Raw API response dictionary from MetaAPI.

        Returns:
            GatewayAccountModel instance with adapted data.
        """
        if not response:
            return None

        balance = parse_optional_float(value=response.get("balance", 0)) or 0.0
        equity = parse_optional_float(value=response.get("equity", 0)) or 0.0
        margin = parse_optional_float(value=response.get("margin", 0)) or 0.0
        unrealized_pnl = equity - balance
        balances = self._build_balances(response=response)

        return GatewayAccountModel(
            balances=balances,
            balance=balance,
            nav=equity,
            locked=margin,
            margin=margin,
            exposure=margin,
            pnl=unrealized_pnl,
            response=response,
        )

    def _build_balances(
        self,
        response: Dict[str, Any],
    ) -> List[GatewayAccountBalanceModel]:
        """
        Build list of balance models from API response.

        MetaAPI returns a single currency account, so we create one balance entry
        for the account currency.

        Args:
            response: Raw API response dictionary containing account data.

        Returns:
            List with a single GatewayAccountBalanceModel for the account currency.
        """
        balances: List[GatewayAccountBalanceModel] = []

        currency = response.get("currency", "USD")
        balance = parse_optional_float(value=response.get("balance", 0)) or 0.0
        margin = parse_optional_float(value=response.get("margin", 0)) or 0.0

        balances.append(
            GatewayAccountBalanceModel(
                asset=currency,
                balance=balance,
                locked=margin,
                response=response,
            )
        )

        return balances

    def _check_credentials(self) -> bool:
        """
        Check if API credentials are configured.

        Verifies that both auth_token and account_id are set in the configuration.

        Returns:
            True if both credentials are configured, False otherwise.
        """
        return bool(self._config.auth_token and self._config.account_id)

    def _check_trading_allowed(
        self,
        response: Optional[Dict[str, Any]],
    ) -> bool:
        """
        Check if trading is enabled for the account.

        Args:
            response: Raw API response dictionary from MetaAPI.

        Returns:
            True if trading is allowed (tradeAllowed is True), False otherwise.
        """
        if not response:
            return False

        return response.get("tradeAllowed", False)
