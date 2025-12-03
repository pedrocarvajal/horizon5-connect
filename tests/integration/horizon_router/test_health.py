import unittest

from providers.horizon_router import HorizonRouterProvider


class TestHealthResource(unittest.TestCase):
    def setUp(self) -> None:
        self._provider = HorizonRouterProvider()

    def test_health_check(self) -> None:
        response = self._provider.health().check()
        assert response is not None, "Health check response should not be None"
        assert isinstance(response, dict), "Health check response should be a dictionary"
