from services.logging import LoggingService
from services.strategy import StrategyService


class TestStrategy(StrategyService):
    _enabled = True
    _name = "Test"

    def __init__(self) -> None:
        super().__init__()

        self._log = LoggingService()
        self._log.setup("test_strategy")
