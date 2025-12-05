"""Authentication service for session management and user login."""

import json
import time
from pathlib import Path
from typing import Any, Dict, Optional

import questionary

from helpers.get_env import get_env
from interfaces.authentication import AuthenticationInterface
from providers.horizon_router import HorizonRouterProvider
from services.logging import LoggingService

SESSION_FILE_PATH = Path(".horizon-session")
MAX_LOGIN_ATTEMPTS = 3
TOKEN_EXPIRY_BUFFER_SECONDS = 300
MIN_PASSWORD_LENGTH = 8

ENV_TEST_EMAIL = "HORIZON_ROUTER_TEST_EMAIL"
ENV_TEST_PASSWORD = "HORIZON_ROUTER_TEST_PASSWORD"


class AuthenticationService(AuthenticationInterface):
    """Authentication service for managing user sessions and tokens.

    Handles user login, session persistence, token expiration, and automatic
    re-authentication. Sessions are stored in .horizon-session file.

    Attributes:
        _token: JWT authentication token.
        _token_exp: Token expiration timestamp in seconds.
        _user: User data from login.
        _log: Logging service instance.
        _email: Email from registration for auto-login.
        _password: Password from registration for auto-login.
    """

    _token: Optional[str]
    _token_exp: Optional[int]
    _user: Optional[Dict[str, Any]]
    _log: LoggingService
    _email: Optional[str]
    _password: Optional[str]

    def __init__(self) -> None:
        """Initialize authentication service with empty session."""
        self._token = None
        self._token_exp = None
        self._user = None
        self._email = None
        self._password = None
        self._log = LoggingService()

    def setup(self) -> bool:
        """Load session and authenticate if needed.

        Returns:
            True if authenticated successfully, False otherwise.
        """
        self._load_session()

        if self._token and not self._is_token_expired():
            if self._validate_token():
                self._log.info("Session loaded from file")
                return True

            self._log.warning("Session token invalid, authentication required")
            self._clear_session()

        elif self._token and self._is_token_expired():
            self._log.warning("Session expired, authentication required")
            self._clear_session()

        else:
            self._log.info("No session found, authentication required")

        return self._ensure_authenticated()

    def _validate_token(self) -> bool:
        try:
            provider = HorizonRouterProvider()
            provider.me()
            return True
        except Exception:
            return False

    def _clear_session(self) -> None:
        self._token = None
        self._token_exp = None
        self._user = None

        if SESSION_FILE_PATH.exists():
            SESSION_FILE_PATH.unlink()

    def _ensure_authenticated(self) -> bool:
        self._log.warning("Authentication required to continue")

        if self._try_test_credentials():
            return True

        has_account = questionary.confirm(
            "",
            qmark=self._log.prompt("Do you have an account?"),
            default=True,
        ).ask()

        if has_account is None:
            return False

        if not has_account and not self._register():
            return False

        if self._email and self._password:
            if self._login_with_credentials(self._email, self._password):
                self._email = None
                self._password = None
                return True

            self._email = None
            self._password = None

        for attempt in range(1, MAX_LOGIN_ATTEMPTS + 1):
            if self._login():
                return True

            remaining = MAX_LOGIN_ATTEMPTS - attempt

            if remaining > 0:
                self._log.warning(f"Login failed. {remaining} attempt(s) remaining.")
            else:
                self._log.error("Maximum login attempts reached. Exiting.")

        return False

    def _try_test_credentials(self) -> bool:
        test_email = get_env(ENV_TEST_EMAIL)
        test_password = get_env(ENV_TEST_PASSWORD)

        if not test_email or not test_password:
            return False

        self._log.info("Test credentials detected, attempting auto-login")

        if self._login_with_credentials(test_email, test_password):
            return True

        self._log.warning("Auto-login with test credentials failed")
        return False

    def _is_authenticated(self) -> bool:
        return self._token is not None and not self._is_token_expired()

    def _register(self) -> bool:
        self._log.info("Creating a new account")

        name = questionary.text("", qmark=self._log.prompt("Full name:")).ask()
        email = questionary.text("", qmark=self._log.prompt("Email:")).ask()
        password = questionary.password("", qmark=self._log.prompt("Password (min 8 chars):")).ask()
        password_confirmation = questionary.password("", qmark=self._log.prompt("Confirm password:")).ask()

        if not name or not email or not password or not password_confirmation:
            self._log.error("All fields are required")
            return False

        if password != password_confirmation:
            self._log.error("Passwords do not match")
            return False

        if len(password) < MIN_PASSWORD_LENGTH:
            self._log.error(f"Password must be at least {MIN_PASSWORD_LENGTH} characters")
            return False

        try:
            provider = HorizonRouterProvider()
            response = provider.register(name, email, password, password_confirmation)
            user_id = response["data"]["id"]
            self._log.success("Account created successfully.")
            self._log.info(f"User data: {response['data']}")
            self._log.warning("Please check your email to activate your account.")

            if not self._verify_email(provider, user_id):
                return False

            self._email = email
            self._password = password
            return True

        except Exception as exception:
            self._log.error(f"Registration failed: {exception}")
            return False

    def _verify_email(self, provider: HorizonRouterProvider, user_id: str) -> bool:
        token = questionary.text("", qmark=self._log.prompt("Verification token:")).ask()

        if not token:
            self._log.error("Verification token is required")
            return False

        try:
            provider.verify_email(user_id, token)
            self._log.success("Email verified successfully.")
            return True

        except Exception as exception:
            self._log.error(f"Email verification failed: {exception}")
            return False

    def _login_with_credentials(self, email: str, password: str) -> bool:
        try:
            provider = HorizonRouterProvider()
            login_response = provider.login(email, password)
            token = login_response["data"]["token"]
            expires_in = login_response["data"]["expires_in"]

            if not token:
                self._log.error("Authentication failed: no token received")
                return False

            user_response = provider.me()
            self._user = user_response["data"]

            self._token = token
            self._token_exp = int(time.time()) + expires_in
            self._save_session()
            self._log.success("Authentication successful")
            return True

        except Exception as exception:
            self._log.error(f"Authentication failed: {exception}")
            return False

    def _login(self) -> bool:
        email = questionary.text("", qmark=self._log.prompt("Email:")).ask()
        password = questionary.password("", qmark=self._log.prompt("Password:")).ask()

        if not email or not password:
            self._log.error("Email and password are required")
            return False

        try:
            provider = HorizonRouterProvider()
            login_response = provider.login(email, password)
            token = login_response["data"]["token"]
            expires_in = login_response["data"]["expires_in"]

            if not token:
                self._log.error("Authentication failed: no token received")
                return False

            user_response = provider.me()
            self._user = user_response["data"]

            self._token = token
            self._token_exp = int(time.time()) + expires_in
            self._save_session()
            self._log.success("Authentication successful")
            return True

        except Exception as exception:
            self._log.error(f"Authentication failed: {exception}")
            return False

    def _is_token_expired(self) -> bool:
        if self._token is None or self._token_exp is None:
            return True

        current_time = int(time.time())
        return current_time >= (self._token_exp - TOKEN_EXPIRY_BUFFER_SECONDS)

    def _load_session(self) -> None:
        if not SESSION_FILE_PATH.exists():
            return

        try:
            content = SESSION_FILE_PATH.read_text()
            data = json.loads(content)
            self._token = data.get("token")
            self._token_exp = data.get("exp")
            self._user = data.get("user")
        except (json.JSONDecodeError, OSError) as exception:
            self._log.warning(f"Failed to load session: {exception}")
            self._token = None
            self._token_exp = None
            self._user = None

    def _save_session(self) -> None:
        if not self._token:
            return

        try:
            data = {"token": self._token, "exp": self._token_exp, "user": self._user}
            SESSION_FILE_PATH.write_text(json.dumps(data))
            self._log.info(f"Session saved to {SESSION_FILE_PATH}")
        except OSError as exception:
            self._log.error(f"Failed to save session: {exception}")


__all__ = ["AuthenticationService"]
