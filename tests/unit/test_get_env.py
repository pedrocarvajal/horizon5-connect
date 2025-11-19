import os
import unittest
from unittest.mock import patch

from helpers.get_env import get_env


class TestGetEnv(unittest.TestCase):
    @patch.dict(os.environ, {"TEST_KEY": "test_value"})
    def test_get_env_with_existing_key(self) -> None:
        assert get_env("TEST_KEY") == "test_value"

    def test_get_env_with_non_existing_key_no_default(self) -> None:
        assert get_env("NON_EXISTING_KEY") is None

    def test_get_env_with_non_existing_key_with_default(self) -> None:
        assert get_env("NON_EXISTING_KEY", "default_value") == "default_value"

    @patch.dict(os.environ, {"EXISTING_KEY": "existing_value"}, clear=True)
    def test_get_env_with_existing_key_and_default(self) -> None:
        assert get_env("EXISTING_KEY", "default_value") == "existing_value"

