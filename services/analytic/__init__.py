from models.tick import TickModel
from models.trade import TradeModel
from services.logging import LoggingService


class AnalyticService:
    def __init__(self) -> None:
        self._log = LoggingService()
        self._log.setup("analytic_service")

    def setup(self) -> None:
        pass

    def on_tick(self, tick: TickModel) -> None:
        pass

    def on_transaction(self, trade: TradeModel) -> None:
        pass

    def on_end(self) -> None:
        pass
