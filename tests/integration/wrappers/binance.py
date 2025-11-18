import unittest

from services.gateway import GatewayService
from services.logging import LoggingService


class BinanceWrapper(unittest.TestCase):
    _gateway: GatewayService
    _log: LoggingService

    def setUp(self) -> None:
        self._log = LoggingService()
        self._log.setup(name=self.__class__.__name__)

        self._gateway = GatewayService(
            gateway="binance",
            futures=True,
        )
