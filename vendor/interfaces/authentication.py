"""Authentication interface for provider authentication implementations."""

from abc import ABC, abstractmethod


class AuthenticationInterface(ABC):
    """Abstract base class defining the authentication contract for providers."""

    @abstractmethod
    def setup(self) -> bool:
        """Initialize authentication and validate credentials."""
