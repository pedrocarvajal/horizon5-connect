import unittest
from typing import Any, Dict, Optional
from unittest.mock import MagicMock, patch

import requests

from vendor.enums.http_status import HttpStatus
from vendor.services.gateway.gateways.binance.helpers.execute_request import execute_request


class TestExecuteRequest(unittest.TestCase):
    _TEST_URL: str = "https://api.binance.com/test"
    _TEST_API_KEY: str = "test_key"
    _TEST_API_SECRET: str = "test_secret"
    _TEST_SYMBOL: str = "BTCUSDT"

    def _create_mock_response(
        self,
        status_code: int,
        json_data: Optional[Dict[str, Any]] = None,
        text: str = "OK",
    ) -> MagicMock:
        mock_response = MagicMock()
        mock_response.status_code = status_code
        mock_response.text = text

        if json_data is not None:
            mock_response.json.return_value = json_data

        return mock_response

    @patch("vendor.services.gateway.gateways.binance.helpers.execute_request.requests.get")
    def test_execute_request_returns_json_on_get_success(
        self,
        mock_get: MagicMock,
    ) -> None:
        mock_get.return_value = self._create_mock_response(
            status_code=HttpStatus.OK.value,
            json_data={"data": "success"},
        )

        result = execute_request(
            method="GET",
            url=self._TEST_URL,
            api_key=self._TEST_API_KEY,
            api_secret=self._TEST_API_SECRET,
            params={"symbol": self._TEST_SYMBOL},
        )

        assert result is not None
        assert result == {"data": "success"}

        mock_get.assert_called_once()

    @patch("vendor.services.gateway.gateways.binance.helpers.execute_request.requests.post")
    def test_execute_request_returns_json_on_post_success(
        self,
        mock_post: MagicMock,
    ) -> None:
        mock_post.return_value = self._create_mock_response(
            status_code=HttpStatus.OK.value,
            json_data={"orderId": "123"},
        )

        result = execute_request(
            method="POST", url=self._TEST_URL, api_key=self._TEST_API_KEY, api_secret=self._TEST_API_SECRET
        )

        assert result is not None
        assert result == {
            "orderId": "123",
        }

    @patch("vendor.services.gateway.gateways.binance.helpers.execute_request.requests.get")
    def test_execute_request_returns_none_on_http_error(
        self,
        mock_get: MagicMock,
    ) -> None:
        mock_get.return_value = self._create_mock_response(
            status_code=HttpStatus.BAD_REQUEST.value,
            text="Bad Request",
        )

        result = execute_request(
            method="GET",
            url=self._TEST_URL,
            api_key=self._TEST_API_KEY,
            api_secret=self._TEST_API_SECRET,
        )

        assert result is None

    @patch("vendor.services.gateway.gateways.binance.helpers.execute_request.requests.get")
    def test_execute_request_returns_none_on_network_error(
        self,
        mock_get: MagicMock,
    ) -> None:
        mock_get.side_effect = requests.exceptions.RequestException("Network error")
        result = execute_request(
            method="GET",
            url=self._TEST_URL,
            api_key=self._TEST_API_KEY,
            api_secret=self._TEST_API_SECRET,
        )

        assert result is None

    @patch("vendor.services.gateway.gateways.binance.helpers.execute_request.requests.get")
    def test_execute_request_calls_log_error_callback_on_failure(
        self,
        mock_get: MagicMock,
    ) -> None:
        mock_get.return_value = self._create_mock_response(
            status_code=HttpStatus.BAD_REQUEST.value,
            text="Bad Request",
        )

        log_was_called = False

        def log_error(_msg: str) -> None:
            nonlocal log_was_called
            log_was_called = True

        result = execute_request(
            method="GET",
            url=self._TEST_URL,
            api_key=self._TEST_API_KEY,
            api_secret=self._TEST_API_SECRET,
            log_error=log_error,
        )

        assert result is None
        assert log_was_called is True

    def test_execute_request_validates_required_parameters(self) -> None:
        test_cases = [
            (
                "empty_api_key",
                "",
                self._TEST_API_SECRET,
                self._TEST_URL,
                "GET",
            ),
            (
                "empty_api_secret",
                self._TEST_API_KEY,
                "",
                self._TEST_URL,
                "GET",
            ),
            (
                "empty_url",
                self._TEST_API_KEY,
                self._TEST_API_SECRET,
                "",
                "GET",
            ),
            (
                "unsupported_method",
                self._TEST_API_KEY,
                self._TEST_API_SECRET,
                self._TEST_URL,
                "PATCH",
            ),
        ]

        for test_name, api_key, api_secret, url, method in test_cases:
            with self.subTest(test_name), self.assertRaises(ValueError):
                execute_request(method=method, url=url, api_key=api_key, api_secret=api_secret)
