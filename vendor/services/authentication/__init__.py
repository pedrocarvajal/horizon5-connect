"""Authentication service for session management and user login."""

import json
from pathlib import Path
from typing import Any, Dict, Optional

import questionary

from vendor.enums.http_status import HttpStatus
from vendor.interfaces.authentication import AuthenticationInterface
from vendor.providers.exceptions import ProviderHTTPError
from vendor.providers.horizon_router import HorizonRouterProvider
from vendor.services.logging import LoggingService

SESSION_FILE_PATH = Path(".horizon-session")


class AuthenticationService(AuthenticationInterface):
    """Authentication service for managing user sessions and tokens.

    Handles token-based authentication and session persistence.
    Sessions are stored in .horizon-session file.

    Attributes:
        _token: JWT authentication token.
        _user: User data from authentication.
        _log: Logging service instance.
    """

    _token: Optional[str]
    _user: Optional[Dict[str, Any]]
    _log: LoggingService

    def __init__(self) -> None:
        """Initialize authentication service with empty session."""
        self._token = None
        self._user = None
        self._log = LoggingService()

    def setup(self) -> bool:
        """Load session and authenticate if needed.

        Returns:
            True if authenticated successfully, False otherwise.
        """
        self._load_session()

        if self._token:
            if self._validate_token():
                self._log.info("Session loaded from file")
                return True

            self._log.warning("Session token invalid, authentication required")
            self._clear_session()
        else:
            self._log.info("No session found, authentication required")

        return self._ensure_authenticated()

    def _authenticate_with_token(self, token: str) -> bool:
        try:
            provider = HorizonRouterProvider()
            provider.set_token(token)
            user_response = provider.me()

            self._user = user_response["data"]
            self._token = token
            self._save_session()
            self._log.success("Authentication successful")

            return True

        except ProviderHTTPError as exception:
            self._log.error(
                "Authentication failed",
                error=str(exception),
            )
            self._handle_auth_error(exception)
            return False

        except Exception as exception:
            self._log.error(
                "Authentication failed",
                error=str(exception),
            )
            return False

    def _handle_auth_error(self, exception: ProviderHTTPError) -> None:
        """Handle authentication error and show IP if rejected."""
        if exception.status_code != HttpStatus.UNAUTHORIZED.value:
            return

        try:
            response_data = json.loads(exception.response_body)
            request_ip = response_data.get("request_ip")

            if request_ip:
                self._log.warning(
                    "Request rejected due to IP restrictions",
                    current_ip=request_ip,
                )

                self._log.info("Add this IP to your token whitelist in the dashboard")
                self._log.info("If using VPN or tunnel, consider disabling it for a stable IP")

        except (json.JSONDecodeError, KeyError):
            pass

    def _clear_session(self) -> None:
        self._token = None
        self._user = None

        if SESSION_FILE_PATH.exists():
            SESSION_FILE_PATH.unlink()

    def _ensure_authenticated(self) -> bool:
        self._log.warning("Authentication required to continue")

        has_account = questionary.confirm(
            "",
            qmark=self._log.prompt("Do you have an account?"),
            default=True,
        ).ask()

        if has_account is None:
            return False

        if not has_account:
            self._log.info("Please create an account at your Horizon5 dashboard")
            self._log.info("Once registered, copy your token and run this command again")
            return False

        return self._request_token()

    def _is_authenticated(self) -> bool:
        return self._token is not None

    def _load_session(self) -> None:
        if not SESSION_FILE_PATH.exists():
            return

        try:
            content = SESSION_FILE_PATH.read_text()
            data = json.loads(content)
            self._token = data.get("token")
            self._user = data.get("user")
        except (json.JSONDecodeError, OSError) as exception:
            self._log.warning(
                "Failed to load session",
                error=str(exception),
            )
            self._token = None
            self._user = None

    def _request_token(self) -> bool:
        token = questionary.password(
            "",
            qmark=self._log.prompt("Enter your token:"),
        ).ask()

        if not token:
            self._log.error("Token is required")
            return False

        token = token.strip()

        if token.lower().startswith("bearer "):
            token = token[7:]

        return self._authenticate_with_token(token)

    def _save_session(self) -> None:
        if not self._token:
            return

        try:
            data = {"token": self._token, "user": self._user}
            SESSION_FILE_PATH.write_text(json.dumps(data))
            self._log.info(
                "Session saved",
                file=str(SESSION_FILE_PATH),
            )

        except OSError as exception:
            self._log.error(
                "Failed to save session",
                error=str(exception),
            )

    def _validate_token(self) -> bool:
        try:
            provider = HorizonRouterProvider()
            provider.me()
            return True
        except Exception:
            return False


__all__ = ["AuthenticationService"]
