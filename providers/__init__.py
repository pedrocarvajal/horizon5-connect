import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import requests

class BaseProvider(ABC):
    _base_url: str
    _headers: Dict[str, str]
    _timeout: int
    _retry_times: int
    _retry_delay: int

    def __init__(self, base_url: str, headers: Optional[Dict[str, str]]=None, timeout: int=30, retry_times: int=3, retry_delay: int=100) -> None:
        self._base_url = base_url.rstrip('/')
        self._headers = headers or {}
        self._timeout = timeout
        self._retry_times = retry_times
        self._retry_delay = retry_delay
        self._validate_configuration()

    @abstractmethod
    def get_service_name(self) -> str:
        pass

    def get(self, endpoint: str, query: Optional[Dict[str, Any]]=None, headers: Optional[Dict[str, str]]=None) -> Dict[str, Any]:
        return self._request('GET', endpoint, query=query, headers=headers)

    def post(self, endpoint: str, data: Optional[Dict[str, Any]]=None, headers: Optional[Dict[str, str]]=None) -> Dict[str, Any]:
        return self._request('POST', endpoint, data=data, headers=headers)

    def put(self, endpoint: str, data: Optional[Dict[str, Any]]=None, headers: Optional[Dict[str, str]]=None) -> Dict[str, Any]:
        return self._request('PUT', endpoint, data=data, headers=headers)

    def patch(self, endpoint: str, data: Optional[Dict[str, Any]]=None, headers: Optional[Dict[str, str]]=None) -> Dict[str, Any]:
        return self._request('PATCH', endpoint, data=data, headers=headers)

    def delete(self, endpoint: str, data: Optional[Dict[str, Any]]=None, headers: Optional[Dict[str, str]]=None) -> Dict[str, Any]:
        return self._request('DELETE', endpoint, data=data, headers=headers)

    def _request(self, method: str, endpoint: str, query: Optional[Dict[str, Any]]=None, data: Optional[Dict[str, Any]]=None, headers: Optional[Dict[str, str]]=None) -> Dict[str, Any]:
        url = self._build_url(endpoint)
        merged_headers = {**self._headers, **(headers or {})}
        attempts = 0
        last_exception: Optional[Exception] = None
        while attempts < self._retry_times:
            try:
                response = requests.request(method=method, url=url, headers=merged_headers, json=data, params=query, timeout=self._timeout)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.Timeout as e:
                attempts += 1
                last_exception = e
                if attempts < self._retry_times:
                    time.sleep(self._retry_delay / 1000)
            except requests.exceptions.ConnectionError as e:
                attempts += 1
                last_exception = e
                if attempts < self._retry_times:
                    time.sleep(self._retry_delay / 1000)
            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code if e.response is not None else 0
                if status_code in (429, 500, 502, 503, 504):
                    attempts += 1
                    last_exception = e
                    if attempts < self._retry_times:
                        time.sleep(self._retry_delay / 1000)
                else:
                    raise RuntimeError(f'{self.get_service_name()} API request failed with status {status_code}: {e!s}') from e
            except requests.exceptions.RequestException as e:
                raise RuntimeError(f'{self.get_service_name()} API request failed: {e!s}') from e
        raise RuntimeError(f'{self.get_service_name()} API request failed after {self._retry_times} attempts: {last_exception!s}')

    def _build_url(self, endpoint: str) -> str:
        endpoint = endpoint.lstrip('/')
        return f'{self._base_url}/{endpoint}'

    def _validate_configuration(self) -> None:
        if not self._base_url:
            raise RuntimeError(f'Base URL not configured for service: {self.get_service_name()}')

    def _sanitize_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        sensitive_keys = {'password', 'master_password', 'investor_password', 'token', 'secret', 'key', 'authorization', 'bearer', 'api_key'}
        sensitive_substrings = ('password', 'token', 'secret', 'key')
        sanitized: Dict[str, Any] = {}
        for key, value in data.items():
            lower_key = key.lower()
            if isinstance(value, dict):
                sanitized[key] = self._sanitize_sensitive_data(value)
            elif any((s in lower_key for s in sensitive_substrings)) or lower_key in sensitive_keys:
                sanitized[key] = '...'
            else:
                sanitized[key] = value
        return sanitized
__all__ = ['BaseProvider']
