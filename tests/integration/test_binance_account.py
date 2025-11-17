import unittest

from services.gateway import GatewayService
from services.gateway.models.gateway_account import GatewayAccountModel
from services.logging import LoggingService


class TestBinanceAccount(unittest.TestCase):
    _log: LoggingService

    def setUp(self) -> None:
        self._log = LoggingService()
        self._log.setup("test_binance_account")

    def test_get_futures_account(self) -> None:
        gateway = GatewayService(
            "binance",
            futures=True,
        )

        self._log.info("Getting futures account information")

        account_info = gateway.account()

        assert account_info is not None, "Account info should not be None"
        assert isinstance(account_info, GatewayAccountModel), (
            "Account info should be a GatewayAccountModel"
        )

        self._log.info("Account info retrieved successfully")
        self._log.info(f"Account balances: {len(account_info.balances)}")

        for balance in account_info.balances:
            if balance.balance and balance.balance > 0:
                self._log.info(
                    f"Asset: {balance.asset}, "
                    f"Balance: {balance.balance}, "
                    f"Locked: {balance.locked}"
                )

        self._log.info(f"Total Balance: {account_info.balance}")
        self._log.info(f"NAV: {account_info.nav}")
        self._log.info(f"Margin: {account_info.margin}")
        self._log.info(f"PNL: {account_info.pnl}")

    def test_get_spot_account(self) -> None:
        gateway = GatewayService(
            "binance",
            futures=False,
        )

        self._log.info("Getting spot account information")

        account_info = gateway.account()

        assert account_info is not None, "Account info should not be None"
        assert isinstance(account_info, GatewayAccountModel), (
            "Account info should be a GatewayAccountModel"
        )

        self._log.info("Account info retrieved successfully")

        for balance in account_info.balances:
            if balance.balance > 0 or balance.locked > 0:
                self._log.info(
                    f"Asset: {balance.asset}, "
                    f"Balance: {balance.balance}, "
                    f"Locked: {balance.locked}"
                )

        self._log.info(f"Total Balance: {account_info.balance}")
        self._log.info(f"NAV: {account_info.nav}")
        self._log.info(f"Locked: {account_info.locked}")
