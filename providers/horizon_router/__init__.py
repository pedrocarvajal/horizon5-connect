"""Horizon Router API provider for user management and authentication."""

import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from helpers.get_env import get_env
from providers import BaseProvider

SESSION_FILE_PATH = Path(".horizon-session")


class HorizonRouterProvider(BaseProvider):
    """Provider for Horizon Router API integration.

    Handles authentication and user management operations through the
    Horizon Router REST API. Reads token from session file.

    Attributes:
        _horizon_base_url: Base URL for the Horizon Router API.
        _session: Session data including token and user.
    """

    _horizon_base_url: str
    _session: Optional[Dict[str, Any]]

    def __init__(self) -> None:
        """Initialize the Horizon Router provider."""
        self._horizon_base_url = self._load_base_url()

        super().__init__(
            base_url=self._horizon_base_url,
            headers=self._setup_headers(),
            timeout=30,
        )

        self._session = self._load_session()

        if self._session and self._session.get("token"):
            self._headers["Authorization"] = f"Bearer {self._session['token']}"

    def user_update(self, user_id: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Update an existing user.

        Args:
            user_id: Unique identifier of the user.
            data: User update data.

        Returns:
            API response with updated user.
        """
        return self.put(
            f"/api/v1/user/{user_id}",
            data=data,
        )

    def backtest_get(self, backtest_id: str) -> Dict[str, Any]:
        """Retrieve backtest by ID.

        Args:
            backtest_id: Backtest identifier.

        Returns:
            API response with backtest data.
        """
        return self.get(f"/api/v1/backtest/{backtest_id}")

    def backtest_create(
        self,
        settings: Dict[str, Any],
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create new backtest for the authenticated user.

        Args:
            settings: Backtest configuration (required).
            status: Optional backtest status.

        Returns:
            API response with created backtest.
        """
        data: Dict[str, Any] = {"settings": settings}

        if status is not None:
            data["status"] = status

        return self.post(
            "/api/v1/backtest",
            data=data,
        )

    def backtest_update(
        self,
        backtest_id: str,
        status: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Update existing backtest.

        Args:
            backtest_id: Backtest identifier.
            status: Optional new backtest status.
            settings: Optional updated backtest configuration.

        Returns:
            API response with updated backtest.
        """
        data: Dict[str, Any] = {}

        if status is not None:
            data["status"] = status

        if settings is not None:
            data["settings"] = settings

        return self.put(
            f"/api/v1/backtest/{backtest_id}",
            data=data,
        )

    def me(self) -> Dict[str, Any]:
        """Get current authenticated user.

        Returns:
            API response with user data.
        """
        return self.get("/api/v1/auth/me")

    def set_token(self, token: str) -> None:
        """Set the authentication token manually.

        Args:
            token: Bearer token to use for authentication.
        """
        self._headers["Authorization"] = f"Bearer {token}"

    def refresh(self) -> Tuple[str, int]:
        """Refresh the current JWT token.

        Returns:
            Tuple of (new JWT token, expires_in seconds).
        """
        response = self.post("/api/v1/auth/refresh")
        token: str = response["data"]["token"]
        expires_in: int = response["data"]["expires_in"]
        self._headers["Authorization"] = f"Bearer {token}"
        return token, expires_in

    def _load_base_url(self) -> str:
        """Load base URL from environment.

        Returns:
            Base URL for API requests.

        Raises:
            ValueError: If environment variable is not set.
        """
        base_url = get_env("HORIZON_ROUTER_BASE_URL", required=False) or ""

        if not base_url:
            raise ValueError("HORIZON_ROUTER_BASE_URL environment variable is not set.")

        return base_url

    def _load_session(self) -> Optional[Dict[str, Any]]:
        """Load session from file.

        Returns:
            Session data if file exists and is valid, None otherwise.
        """
        if not SESSION_FILE_PATH.exists():
            return None

        try:
            content = SESSION_FILE_PATH.read_text()
            return json.loads(content)
        except (json.JSONDecodeError, OSError):
            return None


__all__ = ["HorizonRouterProvider"]
