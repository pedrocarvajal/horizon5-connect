from interfaces.analytic import AnalyticInterface
from models.tick import TickModel
from services.logging import LoggingService


class AnalyticService(AnalyticInterface):
    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    _allocation: float
    _balance: float

    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(self, allocation: float, balance: float) -> None:
        self._log = LoggingService()
        self._log.setup("analytic_service")

        self._allocation = allocation
        self._balance = balance

    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def on_tick(self, tick: TickModel) -> None:
        self._log.info(f"Tick: {tick.date} | Price: {tick.price}")

    def on_end(self) -> None:
        self._log.info("Ending...")
