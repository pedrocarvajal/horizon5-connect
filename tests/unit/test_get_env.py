# Code reviewed on 2025-11-21 by Pedro Carvajal

import os
import unittest
from unittest.mock import patch

from helpers.get_env import get_env


class TestGetEnv(unittest.TestCase):
    # ───────────────────────────────────────────────────────────
    # CONSTANTS
    # ───────────────────────────────────────────────────────────
    _TEST_KEY: str = "TEST_KEY"
    _TEST_VALUE: str = "test_value"
    _NON_EXISTING_KEY: str = "NON_EXISTING_KEY"
    _DEFAULT_VALUE: str = "default_value"
    _EXISTING_KEY: str = "EXISTING_KEY"
    _EXISTING_VALUE: str = "existing_value"

    # ───────────────────────────────────────────────────────────
    # SUCCESS CASES
    # ───────────────────────────────────────────────────────────
    @patch.dict(os.environ, {"TEST_KEY": "test_value"})
    def test_get_env_returns_value_for_existing_key(self) -> None:
        """Verify get_env returns value when environment variable exists."""
        result = get_env(self._TEST_KEY)

        assert result == self._TEST_VALUE

    @patch.dict(os.environ, {"EXISTING_KEY": "existing_value"}, clear=True)
    def test_get_env_returns_existing_value_over_default(self) -> None:
        """Verify get_env returns existing value even when default is provided."""
        result = get_env(self._EXISTING_KEY, self._DEFAULT_VALUE)

        assert result == self._EXISTING_VALUE

    # ───────────────────────────────────────────────────────────
    # EDGE CASES
    # ───────────────────────────────────────────────────────────
    def test_get_env_returns_none_for_non_existing_key(self) -> None:
        """Verify get_env returns None when key does not exist and no default provided."""
        result = get_env(self._NON_EXISTING_KEY)

        assert result is None

    def test_get_env_returns_default_for_non_existing_key(self) -> None:
        """Verify get_env returns default value when key does not exist."""
        result = get_env(self._NON_EXISTING_KEY, self._DEFAULT_VALUE)

        assert result == self._DEFAULT_VALUE
