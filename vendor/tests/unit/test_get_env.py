import os
import unittest
from unittest.mock import patch

from vendor.helpers.get_env import get_env


class TestGetEnv(unittest.TestCase):
    _TEST_KEY: str = "TEST_KEY"
    _TEST_VALUE: str = "test_value"
    _NON_EXISTING_KEY: str = "NON_EXISTING_KEY"
    _DEFAULT_VALUE: str = "default_value"
    _EXISTING_KEY: str = "EXISTING_KEY"
    _EXISTING_VALUE: str = "existing_value"

    @patch.dict(os.environ, {"TEST_KEY": "test_value"})
    def test_get_env_returns_value_for_existing_key(self) -> None:
        result = get_env(self._TEST_KEY)

        assert result == self._TEST_VALUE

    @patch.dict(os.environ, {"EXISTING_KEY": "existing_value"}, clear=True)
    def test_get_env_returns_existing_value_over_default(self) -> None:
        result = get_env(
            self._EXISTING_KEY,
            self._DEFAULT_VALUE,
        )

        assert result == self._EXISTING_VALUE

    def test_get_env_returns_none_for_non_existing_key(self) -> None:
        result = get_env(self._NON_EXISTING_KEY)

        assert result is None

    def test_get_env_returns_default_for_non_existing_key(self) -> None:
        result = get_env(
            self._NON_EXISTING_KEY,
            self._DEFAULT_VALUE,
        )

        assert result == self._DEFAULT_VALUE
