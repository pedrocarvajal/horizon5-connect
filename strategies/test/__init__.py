from services.logging import LoggingService
from services.strategy import StrategyService


class TestStrategy(StrategyService):
    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    _enabled = True
    _name = "Test"

    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(self) -> None:
        super().__init__()

        self._log = LoggingService()
        self._log.setup("test_strategy")
