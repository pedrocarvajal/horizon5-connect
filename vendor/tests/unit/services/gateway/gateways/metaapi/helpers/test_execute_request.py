import unittest
from typing import Any, Dict, Optional
from unittest.mock import MagicMock, patch

import requests

from vendor.enums.http_status import HttpStatus
from vendor.services.gateway.gateways.metaapi.helpers.execute_request import execute_request


class TestExecuteRequest(unittest.TestCase):
    _TEST_URL: str = "https://mt-client-api-v1.agiliumtrade.agiliumtrade.ai/test"
    _TEST_AUTH_TOKEN: str = "test_jwt_token"

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

    @patch("vendor.services.gateway.gateways.metaapi.helpers.execute_request.requests.get")
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
            auth_token=self._TEST_AUTH_TOKEN,
            params={"symbol": "EURUSD"},
        )

        assert result is not None
        assert result == {"data": "success"}

        mock_get.assert_called_once()

    @patch("vendor.services.gateway.gateways.metaapi.helpers.execute_request.requests.post")
    def test_execute_request_returns_json_on_post_success(
        self,
        mock_post: MagicMock,
    ) -> None:
        mock_post.return_value = self._create_mock_response(
            status_code=HttpStatus.OK.value,
            json_data={"orderId": "123"},
        )

        result = execute_request(
            method="POST",
            url=self._TEST_URL,
            auth_token=self._TEST_AUTH_TOKEN,
        )

        assert result is not None
        assert result == {"orderId": "123"}

    @patch("vendor.services.gateway.gateways.metaapi.helpers.execute_request.requests.put")
    def test_execute_request_returns_json_on_put_success(
        self,
        mock_put: MagicMock,
    ) -> None:
        mock_put.return_value = self._create_mock_response(
            status_code=HttpStatus.OK.value,
            json_data={"updated": True},
        )

        result = execute_request(
            method="PUT",
            url=self._TEST_URL,
            auth_token=self._TEST_AUTH_TOKEN,
        )

        assert result is not None
        assert result == {"updated": True}

    @patch("vendor.services.gateway.gateways.metaapi.helpers.execute_request.requests.delete")
    def test_execute_request_returns_json_on_delete_success(
        self,
        mock_delete: MagicMock,
    ) -> None:
        mock_delete.return_value = self._create_mock_response(
            status_code=HttpStatus.OK.value,
            json_data={"deleted": True},
        )

        result = execute_request(
            method="DELETE",
            url=self._TEST_URL,
            auth_token=self._TEST_AUTH_TOKEN,
        )

        assert result is not None
        assert result == {"deleted": True}

    @patch("vendor.services.gateway.gateways.metaapi.helpers.execute_request.requests.get")
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
            auth_token=self._TEST_AUTH_TOKEN,
        )

        assert result is None

    @patch("vendor.services.gateway.gateways.metaapi.helpers.execute_request.requests.get")
    def test_execute_request_returns_none_on_network_error(
        self,
        mock_get: MagicMock,
    ) -> None:
        mock_get.side_effect = requests.exceptions.RequestException("Network error")

        result = execute_request(
            method="GET",
            url=self._TEST_URL,
            auth_token=self._TEST_AUTH_TOKEN,
        )

        assert result is None

    def test_execute_request_validates_required_parameters(self) -> None:
        test_cases = [
            ("empty_auth_token", "", self._TEST_URL, "GET"),
            ("empty_url", self._TEST_AUTH_TOKEN, "", "GET"),
            ("unsupported_method", self._TEST_AUTH_TOKEN, self._TEST_URL, "PATCH"),
        ]

        for test_name, auth_token, url, method in test_cases:
            with self.subTest(test_name), self.assertRaises(ValueError):
                execute_request(method=method, url=url, auth_token=auth_token)

    @patch("vendor.services.gateway.gateways.metaapi.helpers.execute_request.requests.get")
    def test_execute_request_includes_auth_token_header(
        self,
        mock_get: MagicMock,
    ) -> None:
        mock_get.return_value = self._create_mock_response(
            status_code=HttpStatus.OK.value,
            json_data={},
        )

        execute_request(
            method="GET",
            url=self._TEST_URL,
            auth_token=self._TEST_AUTH_TOKEN,
        )

        call_kwargs = mock_get.call_args.kwargs
        assert "headers" in call_kwargs
        assert call_kwargs["headers"]["auth-token"] == self._TEST_AUTH_TOKEN

    @patch("vendor.services.gateway.gateways.metaapi.helpers.execute_request.requests.get")
    def test_execute_request_returns_list_response(
        self,
        mock_get: MagicMock,
    ) -> None:
        mock_response = MagicMock()
        mock_response.status_code = HttpStatus.OK.value
        mock_response.json.return_value = [{"id": 1}, {"id": 2}]
        mock_get.return_value = mock_response

        result = execute_request(
            method="GET",
            url=self._TEST_URL,
            auth_token=self._TEST_AUTH_TOKEN,
        )

        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 2
