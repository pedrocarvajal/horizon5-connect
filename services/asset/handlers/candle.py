from models.tick import TickModel
from services.logging import LoggingService


class CandleHandler:
    def __init__(self) -> None:
        self._log = LoggingService()
        self._log.setup("candles_handler")

    def setup(self) -> None:
        pass

    def on_tick(self, tick: TickModel) -> None:
        pass

    def on_end(self) -> None:
        pass
