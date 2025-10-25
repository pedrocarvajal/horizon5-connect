from models.tick import TickModel
from models.trade import TradeModel
from services.logging import LoggingService


class AssetInterface:
    _symbol: str

    def __init__(self) -> None:
        self._log = LoggingService()
        self._log.setup(self._symbol)

    def on_start(self) -> None:
        self._log.info(f"Initializing {self._symbol}")

    def on_tick(self, tick: TickModel) -> None:
        pass

    def on_transaction(self, trade: TradeModel) -> None:
        pass

    def on_end(self) -> None:
        pass

    @property
    def source(self) -> str:
        return self._source.lower()

    @source.setter
    def source(self, value: str) -> None:
        self._source = value

    @property
    def symbol(self) -> str:
        return self._symbol.lower()

    @symbol.setter
    def symbol(self, value: str) -> None:
        self._symbol = value

    @property
    def log(self) -> LoggingService:
        return self._log
