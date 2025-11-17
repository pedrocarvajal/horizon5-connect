# Last coding review: 2025-11-17 16:40:03
import unittest
from typing import Optional

from services.gateway import GatewayService
from services.gateway.models.gateway_account import GatewayAccountModel
from services.logging import LoggingService


class TestBinanceAccount(unittest.TestCase):
    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    _log: LoggingService

    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def setUp(self) -> None:
        self._log = LoggingService()
        self._log.setup(name="test_binance_account")

    def test_get_futures_account(self) -> None:
        gateway = self._create_gateway(futures=True)

        self._log.info("Getting futures account information")

        account_info = gateway.account()
        self._validate_account_info(account_info=account_info)

        self._log.info("Account info retrieved successfully")
        self._log.info(f"Account balances: {len(account_info.balances)}")

        self._log_account_balances(account_info=account_info, futures=True)
        self._log_account_summary(account_info=account_info, futures=True)

    def test_get_spot_account(self) -> None:
        gateway = self._create_gateway(futures=False)

        self._log.info("Getting spot account information")

        account_info = gateway.account()
        self._validate_account_info(account_info=account_info)

        self._log.info("Account info retrieved successfully")

        self._log_account_balances(account_info=account_info, futures=False)
        self._log_account_summary(account_info=account_info, futures=False)

    # ───────────────────────────────────────────────────────────
    # PRIVATE METHODS
    # ───────────────────────────────────────────────────────────
    def _create_gateway(self, futures: bool) -> GatewayService:
        return GatewayService(
            gateway="binance",
            futures=futures,
        )

    def _validate_account_info(self, account_info: Optional[GatewayAccountModel]) -> None:
        assert account_info is not None, "Account info should not be None"
        assert isinstance(account_info, GatewayAccountModel), "Account info should be a GatewayAccountModel"

    def _log_account_balances(self, account_info: Optional[GatewayAccountModel], futures: bool) -> None:
        if account_info is None:
            return

        for balance in account_info.balances:
            if futures:
                if balance.balance and balance.balance > 0:
                    self._log.info(f"Asset: {balance.asset}, Balance: {balance.balance}, Locked: {balance.locked}")

            elif balance.balance > 0 or balance.locked > 0:
                self._log.info(f"Asset: {balance.asset}, Balance: {balance.balance}, Locked: {balance.locked}")

    def _log_account_summary(self, account_info: Optional[GatewayAccountModel], futures: bool) -> None:
        if account_info is None:
            return

        self._log.info(f"Total Balance: {account_info.balance}")
        self._log.info(f"NAV: {account_info.nav}")

        if futures:
            self._log.info(f"Margin: {account_info.margin}")
            self._log.info(f"PNL: {account_info.pnl}")
        else:
            self._log.info(f"Locked: {account_info.locked}")
