import unittest
from unittest.mock import MagicMock, patch

import requests

from enums.http_status import HttpStatus
from services.gateway.gateways.binance.helpers.execute_request import execute_request


class TestExecuteRequest(unittest.TestCase):
    @patch("services.gateway.gateways.binance.helpers.execute_request.requests.get")
    def test_execute_request_get_success(self, mock_get: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.status_code = HttpStatus.OK.value
        mock_response.json.return_value = {"data": "success"}
        mock_response.text = "OK"
        mock_get.return_value = mock_response

        result = execute_request(
            method="GET",
            url="https://api.binance.com/test",
            api_key="test_key",
            api_secret="test_secret",
            params={"symbol": "BTCUSDT"},
        )

        assert result is not None
        assert result == {"data": "success"}
        mock_get.assert_called_once()

    @patch("services.gateway.gateways.binance.helpers.execute_request.requests.post")
    def test_execute_request_post_success(self, mock_post: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.status_code = HttpStatus.OK.value
        mock_response.json.return_value = {"orderId": "123"}
        mock_response.text = "OK"
        mock_post.return_value = mock_response

        result = execute_request(
            method="POST",
            url="https://api.binance.com/test",
            api_key="test_key",
            api_secret="test_secret",
        )

        assert result is not None
        assert result == {"orderId": "123"}

    @patch("services.gateway.gateways.binance.helpers.execute_request.requests.get")
    def test_execute_request_http_error(self, mock_get: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.status_code = HttpStatus.BAD_REQUEST.value
        mock_response.text = "Bad Request"
        mock_get.return_value = mock_response

        result = execute_request(
            method="GET",
            url="https://api.binance.com/test",
            api_key="test_key",
            api_secret="test_secret",
        )

        assert result is None

    @patch("services.gateway.gateways.binance.helpers.execute_request.requests.get")
    def test_execute_request_network_error(self, mock_get: MagicMock) -> None:
        mock_get.side_effect = requests.exceptions.RequestException("Network error")

        result = execute_request(
            method="GET",
            url="https://api.binance.com/test",
            api_key="test_key",
            api_secret="test_secret",
        )

        assert result is None

    def test_execute_request_empty_api_key(self) -> None:
        with self.assertRaises(ValueError):
            execute_request(
                method="GET",
                url="https://api.binance.com/test",
                api_key="",
                api_secret="test_secret",
            )

    def test_execute_request_empty_api_secret(self) -> None:
        with self.assertRaises(ValueError):
            execute_request(
                method="GET",
                url="https://api.binance.com/test",
                api_key="test_key",
                api_secret="",
            )

    def test_execute_request_empty_url(self) -> None:
        with self.assertRaises(ValueError):
            execute_request(
                method="GET",
                url="",
                api_key="test_key",
                api_secret="test_secret",
            )

    def test_execute_request_unsupported_method(self) -> None:
        with self.assertRaises(ValueError):
            execute_request(
                method="PATCH",
                url="https://api.binance.com/test",
                api_key="test_key",
                api_secret="test_secret",
            )

    @patch("services.gateway.gateways.binance.helpers.execute_request.requests.get")
    def test_execute_request_with_log_error(self, mock_get: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.status_code = HttpStatus.BAD_REQUEST.value
        mock_response.text = "Bad Request"
        mock_get.return_value = mock_response

        log_error_called = False

        def log_error(_msg: str) -> None:
            nonlocal log_error_called
            log_error_called = True

        result = execute_request(
            method="GET",
            url="https://api.binance.com/test",
            api_key="test_key",
            api_secret="test_secret",
            log_error=log_error,
        )

        assert result is None
        assert log_error_called is True
