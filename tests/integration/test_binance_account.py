# Last coding review: 2025-11-17 17:49:49

from enums.order_side import OrderSide
from enums.order_type import OrderType
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

    def test_get_verification(self) -> None:
        self._log.info("Opening position to verify account configuration")

        symbol = "BTCUSDT"
        volume = 0.002

        order = self._gateway.place_order(
            symbol=symbol,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            volume=volume,
        )

        assert order is not None, "Order should not be None"
        assert order.id != "", "Order ID should not be empty"
        self._log.info(f"Position opened with order {order.id}")

        verification = self._gateway.get_verification(symbol=symbol)

        assert verification is not None, "Verification should not be None"
        assert isinstance(verification, dict), "Verification should be a dict"
        assert "required_leverage" in verification, "Verification should check required_leverage"
        assert "usdt_balance" in verification, "Verification should check usdt_balance"
        assert "cross_margin" in verification, "Verification should check cross_margin"
        assert "one_way_mode" in verification, "Verification should check one_way_mode"
        assert "trading_permissions" in verification, "Verification should check trading_permissions"

        assert verification["required_leverage"] is True, "Leverage should be >= 1"
        assert verification["usdt_balance"] is True, "USDT balance should be > 0"
        assert verification["cross_margin"] is True, "Should be in cross margin mode"
        assert verification["one_way_mode"] is True, "Should be in one-way mode"
        assert verification["trading_permissions"] is True, "Trading permissions should be enabled"

        self._log.info(f"Closing position for order {order.id}")
        self._close_position(symbol=symbol, order=order)
