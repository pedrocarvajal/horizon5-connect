# Last coding review: 2025-11-17 16:41:48
import unittest

from services.gateway import GatewayService
from services.logging import LoggingService


class TestBinanceLeverage(unittest.TestCase):
    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    _log: LoggingService
    _gateway: GatewayService

    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def setUp(self) -> None:
        self._log = LoggingService()
        self._log.setup(name="test_binance_leverage")
        self._gateway = GatewayService(
            gateway="binance",
            futures=True,
        )

    def test_get_leverage_info(self) -> None:
        self._log.info("Getting leverage info for BTCUSDT")

        leverage_info = self._gateway.get_leverage_info(symbol="btcusdt")

        assert leverage_info is not None, "Leverage info should not be None"
        assert "symbol" in leverage_info, "Leverage info should contain symbol"
        assert "brackets" in leverage_info, "Leverage info should contain brackets"

        self._log.info(f"Leverage info retrieved: {leverage_info}")

        brackets = leverage_info.get("brackets", [])
        assert len(brackets) > 0, "Should have at least one leverage bracket"

        first_bracket = brackets[0]
        assert "initialLeverage" in first_bracket, "Bracket should contain initialLeverage"
        assert "notionalCap" in first_bracket, "Bracket should contain notionalCap"

        self._log.info(f"First bracket: {first_bracket}")

    def test_set_leverage(self) -> None:
        leverage = 3

        self._log.info(f"Setting leverage to {leverage}x for BTCUSDT")

        result = self._gateway.set_leverage(
            symbol="btcusdt",
            leverage=leverage,
        )

        assert result is True, "Leverage should be set successfully"
        self._log.info(f"Leverage set to {leverage}x successfully")

    def test_set_and_get_leverage(self) -> None:
        leverage = 5

        self._log.info(f"Setting leverage to {leverage}x for BTCUSDT")

        set_result = self._gateway.set_leverage(
            symbol="btcusdt",
            leverage=leverage,
        )

        assert set_result is True, "Leverage should be set successfully"

        leverage_info = self._gateway.get_leverage_info(symbol="btcusdt")
        assert leverage_info is not None, "Leverage info should not be None"

        self._log.info(f"Leverage info after setting: {leverage_info}")
