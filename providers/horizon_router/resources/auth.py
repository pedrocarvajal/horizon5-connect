from typing import TYPE_CHECKING, Any, Dict
if TYPE_CHECKING:
    from providers.horizon_router import HorizonRouterProvider

class AuthResource:

    def __init__(self, provider: 'HorizonRouterProvider') -> None:
        self._provider = provider

    def login(self, email: str, password: str) -> Dict[str, Any]:
        return self._provider.post('/api/v1/auth/login', data={'email': email, 'password': password})

    def logout(self) -> Dict[str, Any]:
        return self._provider.post('/api/v1/auth/logout')

    def refresh(self) -> Dict[str, Any]:
        return self._provider.post('/api/v1/auth/refresh')

    def me(self) -> Dict[str, Any]:
        return self._provider.get('/api/v1/auth/me')
