from models.tick import TickModel
from services.logging import LoggingService


class CandlesHandler:
    def __init__(self) -> None:
        self._log = LoggingService()
        self._log.setup("candles_handler")

    def on_start(self) -> None:
        self._log.info(f"Initializing {self._symbol}")

    def on_tick(self, tick: TickModel) -> None:
        pass

    def on_end(self) -> None:
        pass
