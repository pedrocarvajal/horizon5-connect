from interfaces.strategy import StrategyInterface
from models.tick import TickModel
from models.trade import TradeModel
from services.logging import LoggingService


class StrategyService(StrategyInterface):
    def __init__(self) -> None:
        super().__init__()

        self._log = LoggingService()
        self._log.setup("strategy_service")

    def setup(self) -> None:
        self._log.info(f"Setting up {self.name}")

    def on_tick(self, tick: TickModel) -> None:
        pass

    def on_transaction(self, trade: TradeModel) -> None:
        pass

    def on_end(self) -> None:
        pass

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = value
