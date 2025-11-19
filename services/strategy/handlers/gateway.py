# Code reviewed on 2025-11-19 by pedrocarvajal

from typing import Dict

from services.gateway import GatewayService
from services.logging import LoggingService


class GatewayHandler:
    """
    Handler for gateway configuration validation and verification.

    This handler validates gateway configuration and trading requirements
    during initialization. It checks API credentials, account settings,
    leverage configuration, balance, margin mode, position mode, and
    trading permissions. If credentials are not configured, it operates
    in backtest mode with warnings. If credentials are configured but
    requirements are not met, it raises ValueError exceptions.

    Attributes:
        _gateway: Gateway service instance for accessing gateway operations.
        _log: Logging service instance for logging operations.
        _verification: Dictionary containing gateway verification status with
            boolean values for various configuration checks.
    """

    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    _gateway: GatewayService
    _log: LoggingService
    _verification: Dict[str, bool]

    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(
        self,
        gateway: GatewayService,
    ) -> None:
        """
        Initialize the gateway handler.

        Args:
            gateway: Gateway service instance to validate and use.

        Raises:
            ValueError: If gateway verification fails and credentials are configured.
                Specific errors include:
                - Leverage not set to 1x or higher
                - USDT balance is zero
                - Account not in cross margin mode
                - Account not in one-way position mode
                - Trading permissions disabled
        """
        self._log = LoggingService()
        self._log.setup("gateway_handler")

        self._gateway = gateway

        self._verification = self._gateway.get_verification()
        self._validate_gateway_configuration()

    # ───────────────────────────────────────────────────────────
    # PRIVATE METHODS
    # ───────────────────────────────────────────────────────────
    def _validate_gateway_configuration(self) -> None:
        """
        Validate gateway configuration and credentials.

        Checks if API credentials are configured. If not configured, logs
        warnings and allows operation in backtest mode. If configured,
        proceeds to validate trading requirements.

        Raises:
            ValueError: If trading requirements are not met (only when
                credentials are configured).
        """
        credentials_configured = self._verification.get("credentials_configured", False)

        if not credentials_configured:
            self._log.warning("API credentials not configured in gateway config")
            self._log.warning("Operating in backtest mode without live trading capabilities")
            return

        self._check_trading_requirements()

    def _check_trading_requirements(self) -> None:
        """
        Check trading requirements for live trading.

        Validates that all required trading conditions are met:
        - Leverage is set to 1x or higher
        - USDT balance is greater than zero
        - Account is in cross margin mode
        - Account is in one-way position mode
        - Trading permissions are enabled

        Raises:
            ValueError: If any trading requirement is not met, with a
                specific error message describing the issue.
        """
        required_leverage = self._verification.get("required_leverage", False)
        usdt_balance = self._verification.get("usdt_balance", False)
        cross_margin = self._verification.get("cross_margin", False)
        one_way_mode = self._verification.get("one_way_mode", False)
        trading_permissions = self._verification.get("trading_permissions", False)

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
