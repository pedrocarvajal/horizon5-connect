# Last coding review: 2025-11-17 17:49:49


from services.gateway.models.gateway_account import GatewayAccountModel
from tests.integration.wrappers.binance import BinanceWrapper


class TestBinanceAccount(BinanceWrapper):
    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def setUp(self) -> None:
        super().setUp()
        self._log.setup(name="test_binance_account")

    def test_get_futures_account(self) -> None:
        self._log.info("Getting futures account information")

        account_info = self._gateway.get_account()
        assert account_info is not None, "Account info should not be None"
        assert isinstance(account_info, GatewayAccountModel), "Account info should be a GatewayAccountModel"
        assert account_info.balance > 0, f"Balance should be greater than 0, got {account_info.balance}"
        assert account_info.nav > 0, f"NAV should be greater than 0, got {account_info.nav}"
        assert account_info.locked >= 0, f"Locked should be greater than or equal to 0, got {account_info.locked}"
        assert account_info.margin >= 0, f"Margin should be greater than or equal to 0, got {account_info.margin}"
        assert account_info.exposure >= 0, f"Exposure should be greater than or equal to 0, got {account_info.exposure}"
        assert len(account_info.balances) >= 1, f"Balances, got {len(account_info.balances)}"
        assert account_info.response is not None, "Response should not be None"
