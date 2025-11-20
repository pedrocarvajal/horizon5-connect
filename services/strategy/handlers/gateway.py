from typing import Any, Dict

from services.gateway import GatewayService
from services.logging import LoggingService


class GatewayHandler:
    _gateway: GatewayService
    _log: LoggingService
    _verification: Dict[str, bool]

    def __init__(
        self,
        gateway: GatewayService,
        **kwargs: Any,
    ) -> None:
        self._log = LoggingService()
        self._log.setup("gateway_handler")

        self._gateway = gateway
        self._backtest = kwargs.get("backtest", False)
        self._backtest_id = kwargs.get("backtest_id")

        if not self._backtest:
            self._verification = self._gateway.get_verification()
            self._validate_gateway_configuration()

    def _validate_gateway_configuration(self) -> None:
        credentials_configured = self._verification.get("credentials_configured", False)

        if not credentials_configured:
            self._log.warning("API credentials not configured in gateway config")
            self._log.warning("Operating in backtest mode without live trading capabilities")
            return

        self._check_trading_requirements()

    def _check_trading_requirements(self) -> None:
        credentials_configured = self._verification.get("credentials_configured", False)
        required_leverage = self._verification.get("required_leverage", False)
        usdt_balance = self._verification.get("usdt_balance", False)
        cross_margin = self._verification.get("cross_margin", False)
        one_way_mode = self._verification.get("one_way_mode", False)
        trading_permissions = self._verification.get("trading_permissions", False)

        if not credentials_configured:
            raise ValueError("API credentials not configured in gateway config")

        if not required_leverage:
            raise ValueError("Leverage must be set to 1x or higher for the trading symbol")

        if not usdt_balance:
            raise ValueError("USDT balance is zero - deposit funds to enable trading")

        if not cross_margin:
            raise ValueError("Account must be configured in cross margin mode")

        if not one_way_mode:
            raise ValueError("Account must be in one-way position mode (disable hedge mode)")

        if not trading_permissions:
            raise ValueError("Trading permissions disabled - check API key restrictions or account status")

        self._log.success("Gateway configuration validated successfully")
        self._log.success(f"Running sandbox: {self._gateway.sandbox}")
