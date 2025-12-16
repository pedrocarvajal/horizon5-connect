"""Integration tests for MetaAPI account operations."""

from vendor.services.gateway.models.gateway_account import (
    GatewayAccountBalanceModel,
    GatewayAccountModel,
)
from vendor.tests.integration.metaapi.wrappers.metaapi import MetaApiWrapper


class TestMetaApiAccount(MetaApiWrapper):
    """Integration tests for MetaAPI account information retrieval."""

    def setUp(self) -> None:
        super().setUp()

    def test_get_account(self) -> None:
        """Test retrieving account information."""
        account = self._gateway.get_account()
        assert account is not None, "Account should not be None"
        assert isinstance(account, GatewayAccountModel), "Account should be GatewayAccountModel"
        assert account.balance >= 0, "Balance should be >= 0"
        assert account.nav >= 0, "NAV (equity) should be >= 0"
        assert account.margin >= 0, "Margin should be >= 0"
        assert account.response is not None, "Response should not be None"
        assert len(account.balances) > 0, "Should have at least one balance entry"
        for balance in account.balances:
            assert isinstance(balance, GatewayAccountBalanceModel), "Balance should be GatewayAccountBalanceModel"
            assert balance.asset != "", "Asset should not be empty"
            assert balance.balance >= 0, "Balance should be >= 0"
        self._log.info(f"Account balance: {account.balance}, equity: {account.nav}")

    def test_get_verification(self) -> None:
        """Test account verification."""
        verification = self._gateway.get_verification()
        assert verification is not None, "Verification should not be None"
        assert isinstance(verification, dict), "Verification should be a dict"
        assert "credentials_configured" in verification, "Should have credentials_configured key"
        assert "trading_allowed" in verification, "Should have trading_allowed key"
        assert "has_balance" in verification, "Should have has_balance key"
        assert verification["credentials_configured"] is True, "Credentials should be configured"
        self._log.info(f"Verification result: {verification}")
