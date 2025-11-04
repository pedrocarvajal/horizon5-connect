from typing import Any, Dict, Optional

import requests

from helpers.get_env import get_env


class HorizonRouterProvider:
    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    _base_url: str
    _api_key: str
    _headers: Dict[str, str]

    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(self, **kwargs: Any) -> None:
        self._base_url = get_env("HORIZON_ROUTER_BASE_URL")
        self._api_key = get_env("HORIZON_ROUTER_APY_KEY")

        self._prepare_headers()

    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def backtest_create(self, body: Dict[str, Any]) -> Dict[str, Any]:
        return self._execute(
            method="POST",
            url=f"{self._base_url}/api/backtest/",
            query=None,
            body=body,
            headers=None,
        )

    def backtest_update(
        self,
        id: str,
        body: Dict[str, Any],
    ) -> Dict[str, Any]:
        return self._execute(
            method="PUT",
            url=f"{self._base_url}/api/backtest/{id}/",
            query=None,
            body=body,
            headers=None,
        )

    def backtests(
        self,
        query: Dict[str, Any],
    ) -> Dict[str, Any]:
        return self._execute(
            method="GET",
            url=f"{self._base_url}/api/backtests/",
            query=query,
            body=None,
            headers=None,
        )

    # ───────────────────────────────────────────────────────────
    # PRIVATE METHODS
    # ───────────────────────────────────────────────────────────
    def _execute(
        self,
        method: str,
        url: str,
        query: Optional[Dict[str, Any]],
        body: Optional[Dict[str, Any]],
        headers: Optional[Dict[str, str]],
    ) -> Any:
        if query is None:
            query = {}

        if body is None:
            body = {}

        if headers is None:
            headers = {}

        self._headers = {
            **self._headers,
            **headers,
        }

        try:
            response = requests.request(
                method,
                url,
                headers=self._headers,
                json=body,
                params=query,
            )
        except requests.exceptions.RequestException as e:
            raise e

        return response.json()

    def _prepare_headers(self) -> None:
        self._headers = {
            "X-API-Key": self._api_key,
            "Content-Type": "application/json",
        }
