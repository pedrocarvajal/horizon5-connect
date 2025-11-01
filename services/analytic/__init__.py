from models.order import OrderModel
from models.tick import TickModel
from services.logging import LoggingService


class AnalyticService:
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
        pass

    def on_new_hour(self, tick: TickModel) -> None:
        pass

    def on_new_day(self, tick: TickModel) -> None:
        pass

    def on_new_week(self, tick: TickModel) -> None:
        pass

    def on_new_month(self, tick: TickModel) -> None:
        pass

    def on_transaction(self, order: OrderModel) -> None:
        pass

    def on_end(self) -> None:
        self._log.info("Ending...")
