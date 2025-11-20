# Code reviewed on 2025-11-20 by Pedro Carvajal

from enums.order_side import OrderSide
from services.gateway.models.gateway_account import GatewayAccountModel
from tests.integration.binance.wrappers.binance import BinanceWrapper


class TestBinanceAccount(BinanceWrapper):
    # ───────────────────────────────────────────────────────────
    # CONSTANTS
    # ───────────────────────────────────────────────────────────
    _VERIFICATION_REQUIRED_LEVERAGE: str = "required_leverage"
    _VERIFICATION_USDT_BALANCE: str = "usdt_balance"
    _VERIFICATION_CROSS_MARGIN: str = "cross_margin"
    _VERIFICATION_ONE_WAY_MODE: str = "one_way_mode"
    _VERIFICATION_TRADING_PERMISSIONS: str = "trading_permissions"

    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def setUp(self) -> None:
        super().setUp()
        self._log.setup(name="test_binance_account")

    def test_get_futures_account(self) -> None:
        """Test retrieval of futures account information.

        Verifies that the gateway can retrieve account information and that
        all required account fields are present and valid. Validates balance,
        NAV, locked funds, margin, exposure, and balance entries.
        """
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

    def test_get_verification(self) -> None:
        """Test account configuration verification.

        Opens a test position to verify account configuration and trading
        setup. Validates that all required verification checks pass including
        leverage, USDT balance, cross margin mode, one-way mode, and trading
        permissions. Closes the test position after verification.
        """
        order = self._place_test_order(
            symbol=self._SYMBOL,
            side=OrderSide.BUY,
            volume=self._DEFAULT_ORDER_VOLUME,
        )

        assert order is not None, "Order should not be None"
        assert order.id != "", "Order ID should not be empty"

        verification = self._gateway.get_verification(symbol=self._SYMBOL)

        assert verification is not None, "Verification should not be None"
        assert isinstance(verification, dict), "Verification should be a dict"
        assert self._VERIFICATION_REQUIRED_LEVERAGE in verification, "Verification should check required_leverage"
        assert self._VERIFICATION_USDT_BALANCE in verification, "Verification should check usdt_balance"
        assert self._VERIFICATION_CROSS_MARGIN in verification, "Verification should check cross_margin"
        assert self._VERIFICATION_ONE_WAY_MODE in verification, "Verification should check one_way_mode"
        assert self._VERIFICATION_TRADING_PERMISSIONS in verification, "Verification should check trading_permissions"

        assert verification[self._VERIFICATION_REQUIRED_LEVERAGE] is True, "Leverage should be >= 1"
        assert verification[self._VERIFICATION_USDT_BALANCE] is True, "USDT balance should be > 0"
        assert verification[self._VERIFICATION_CROSS_MARGIN] is True, "Should be in cross margin mode"
        assert verification[self._VERIFICATION_ONE_WAY_MODE] is True, "Should be in one-way mode"
        assert verification[self._VERIFICATION_TRADING_PERMISSIONS] is True, "Trading permissions should be enabled"

        self._close_position(symbol=self._SYMBOL, order=order)
