"""Base wrapper for MetaAPI integration tests."""

import unittest

from vendor.helpers.get_env import get_env
from vendor.services.gateway.gateways.metaapi import MetaApi
from vendor.services.logging import LoggingService


class MetaApiWrapper(unittest.TestCase):
    """Base wrapper for MetaAPI integration tests."""

    _SYMBOL: str = "XAUUSD"

    def __init__(self, method_name: str = "runTest") -> None:
        """
        Initialize the MetaAPI wrapper.

        Args:
            method_name: Name of the test method to run.
        """
        super().__init__(method_name)
        self._gateway: MetaApi
        self._log: LoggingService

    def setUp(self) -> None:
        """Set up the test environment."""
        self._log = LoggingService()
        self._validate_configuration()
        self._gateway = MetaApi(
            auth_token=get_env("METAAPI_AUTH_TOKEN"),
            account_id=get_env("METAAPI_ACCOUNT_ID"),
        )

    def _validate_configuration(self) -> None:
        """Validate that required environment variables are configured."""
        auth_token = get_env("METAAPI_AUTH_TOKEN")
        account_id = get_env("METAAPI_ACCOUNT_ID")

        if auth_token is None:
            self.skipTest(
                "METAAPI_AUTH_TOKEN must be configured for tests. Set METAAPI_AUTH_TOKEN in environment variables"
            )
        if auth_token == "":
            self.skipTest("METAAPI_AUTH_TOKEN must not be empty. Set METAAPI_AUTH_TOKEN in environment variables")
        if account_id is None:
            self.skipTest(
                "METAAPI_ACCOUNT_ID must be configured for tests. Set METAAPI_ACCOUNT_ID in environment variables"
            )
        if account_id == "":
            self.skipTest("METAAPI_ACCOUNT_ID must not be empty. Set METAAPI_ACCOUNT_ID in environment variables")
