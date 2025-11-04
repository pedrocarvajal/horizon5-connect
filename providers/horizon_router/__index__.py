from typing import Any, Dict, Optional

import requests

from helpers.get_env import get_env


class HorizonRouterProvider:
    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    _base_url: str
    _api_key: str
    _headers: dict[str, str]

    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(self, **kwargs: Any) -> None:
        self._base_url = get_env("HORIZON_ROUTER_BASE_URL")
        self._api_key = get_env("HORIZON_ROUTER_API_KEY")

        self._prepare_headers()

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
            "x-api-key": self._api_key,
            "Content-Type": "application/json",
        }

    def backtest_create(self, asset: str) -> Dict[str, Any]:
        return self._execute(
            method="POST",
            url=f"{self._base_url}/api/backtest/",
            query=None,
            body={
                "asset": asset,
            },
            headers=None,
        )

    def backtest_update(
        self,
        id: str,
        asset: str | None = None,
        start_at: int | None = None,
        end_at: int | None = None,
        status: str | None = None,
    ) -> Dict[str, Any]:
        url = f"{self._base_url}/api/backtest/{id}/"
        body = {}

        if asset is not None:
            body["asset"] = asset

        if start_at is not None:
            body["start_at"] = start_at

        if end_at is not None:
            body["end_at"] = end_at

        if status is not None:
            body["status"] = status

        return self._execute(
            method="PUT",
            url=url,
            query=None,
            body=body,
            headers=None,
        )

    def backtests(
        self,
        filter_by: str | None = None,
        page: int = 1,
        page_size: int = 10,
        sort: str = "created_at",
        sort_order: str = "desc",
    ) -> Dict[str, Any]:
        url = f"{self._base_url}/api/backtests/"
        query = {
            "page": page,
            "page_size": page_size,
            "sort": sort,
            "sort_order": sort_order,
        }

        if filter_by is not None:
            query["filter_by"] = filter_by

        return self._execute(
            method="GET",
            url=url,
            query=query,
            body=None,
            headers=None,
        )
